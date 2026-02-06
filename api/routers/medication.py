"""Medication lookup endpoint using RAG pipeline."""

import sys
import re
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models import MedicationRequest, MedicationResponse, WatchSummary

router = APIRouter(prefix="/medication", tags=["Medication"])


def detect_language(text: str) -> str:
    """Detect if text is Chinese or English."""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return "zh" if chinese_chars > len(text) * 0.1 else "en"


def extract_drug_name(query: str, response: str) -> str | None:
    """Try to extract the drug name from query or response."""
    # Common drug name patterns
    patterns = [
        r'\b([A-Z][a-z]+(?:in|ol|am|ide|ate|one|ine|ium))\b',  # Common drug suffixes
        r'(?:about|for|of|called|named)\s+([A-Za-z]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()

    return None


def extract_warnings(response: str) -> list[str]:
    """Extract warning statements from the response."""
    warnings = []

    # Common warning patterns
    warning_patterns = [
        r'(?:warning|caution|alert|danger|do not|avoid|never)[:\s]+([^.!?]+[.!?])',
        r'(?:side effects?|adverse|contraindicated)[:\s]+([^.!?]+[.!?])',
        r'(?:pregnant|nursing|children|elderly|liver|kidney)[^.!?]*(?:should not|avoid|caution)[^.!?]+[.!?]',
    ]

    response_lower = response.lower()
    for pattern in warning_patterns:
        matches = re.findall(pattern, response_lower, re.IGNORECASE)
        warnings.extend([m.strip().capitalize() for m in matches[:3]])

    return warnings[:5]  # Limit to 5 warnings


def create_watch_summary(response: str, drug_name: str | None) -> WatchSummary:
    """Create a watch-optimized summary for medication info."""
    # Extract key info for watch display
    sentences = re.split(r'[.!?。！？]', response)
    short_text = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10 and drug_name and drug_name.lower() in sentence.lower():
            if len(sentence) > 47:
                short_text = sentence[:47] + "..."
            else:
                short_text = sentence
            break

    if not short_text and sentences:
        sentence = sentences[0].strip()
        if len(sentence) > 47:
            short_text = sentence[:47] + "..."
        else:
            short_text = sentence if sentence else "Medication info available."

    # Medication responses are informational
    return WatchSummary(
        short=short_text or "Medication info available.",
        severity="low",
        action="info"
    )


@router.post("/lookup", response_model=MedicationResponse)
async def lookup_medication(request: MedicationRequest) -> MedicationResponse:
    """
    Look up medication information using the RAG pipeline.

    This endpoint retrieves drug information including:
    - Dosage recommendations
    - Side effects
    - Drug interactions
    - Contraindications
    - Special population considerations
    """
    try:
        # Import core modules
        from src.retriever import retrieve_with_fallback, format_context
        from src.llm import (
            get_response,
            build_messages,
            translate_to_english
        )
        from src.prompts import get_prompt

        # Detect language
        language = request.language
        if language == "auto":
            language = detect_language(request.query)

        # Prepare query
        query = request.query

        # Translate Chinese queries for better retrieval
        retrieval_query = query
        if language == "zh":
            retrieval_query = await asyncio.to_thread(
                translate_to_english,
                query
            )

        # Retrieve from FDA drugs collection
        results = await asyncio.to_thread(
            retrieve_with_fallback,
            retrieval_query,
            "fda_drugs"
        )

        # Format context for LLM
        context = format_context(results)

        # Build messages with medication prompt
        system_prompt = get_prompt("medication")
        messages = build_messages(
            system_prompt,
            request.query,
            context,
            request.history or []
        )

        # Get LLM response
        full_response = await asyncio.to_thread(
            get_response,
            messages
        )

        # Extract drug name and warnings
        drug_name = extract_drug_name(request.query, full_response)
        warnings = extract_warnings(full_response)

        # Create watch summary
        summary = create_watch_summary(full_response, drug_name)

        return MedicationResponse(
            success=True,
            summary=summary,
            full_response=full_response,
            drug_name=drug_name,
            confidence=results.get("confidence", 0.5),
            confidence_level=results.get("confidence_level", "medium"),
            sources_count=len(results.get("documents", [[]])[0]) if results.get("documents") else 0,
            warnings=warnings if warnings else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "MEDICATION_LOOKUP_ERROR"
            }
        )
