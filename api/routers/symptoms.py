"""Symptom analysis endpoint using RAG pipeline."""

import sys
import re
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models import SymptomRequest, SymptomResponse, WatchSummary, ErrorResponse

router = APIRouter(prefix="/symptoms", tags=["Symptoms"])


def detect_language(text: str) -> str:
    """Detect if text is Chinese or English."""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return "zh" if chinese_chars > len(text) * 0.1 else "en"


def extract_severity(response: str) -> tuple[str, str]:
    """
    Extract severity level and recommended action from LLM response.

    Returns:
        tuple: (severity, action)
    """
    response_lower = response.lower()

    # Emergency indicators
    emergency_keywords = [
        "emergency", "call 911", "go to er", "immediately",
        "life-threatening", "urgent care", "ambulance",
        "chest pain", "difficulty breathing", "stroke",
        "紧急", "急诊", "立即就医", "危险"
    ]
    for keyword in emergency_keywords:
        if keyword in response_lower:
            return "emergency", "emergency"

    # High severity indicators
    high_keywords = [
        "see a doctor", "medical attention", "consult",
        "professional help", "schedule an appointment",
        "within 24 hours", "as soon as possible",
        "就医", "看医生", "专业医疗"
    ]
    for keyword in high_keywords:
        if keyword in response_lower:
            return "high", "see_doctor"

    # Medium severity indicators
    medium_keywords = [
        "monitor", "if symptoms persist", "watch for",
        "may need", "consider seeing", "over-the-counter",
        "观察", "如果症状持续", "注意观察"
    ]
    for keyword in medium_keywords:
        if keyword in response_lower:
            return "medium", "self_care"

    # Default to low severity
    return "low", "self_care"


def create_watch_summary(response: str, severity: str, action: str) -> WatchSummary:
    """Create a watch-optimized summary from the full response."""
    # Extract first meaningful sentence
    sentences = re.split(r'[.!?。！？]', response)
    short_text = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:
            # Truncate to 50 chars
            if len(sentence) > 47:
                short_text = sentence[:47] + "..."
            else:
                short_text = sentence
            break

    if not short_text:
        short_text = "Analysis complete. See details."

    return WatchSummary(
        short=short_text,
        severity=severity,
        action=action
    )


@router.post("/analyze", response_model=SymptomResponse)
async def analyze_symptoms(
    request: SymptomRequest,
    platform: Optional[str] = Query(default=None, description="Client platform: 'watch' for concise output")
) -> SymptomResponse:
    """
    Analyze symptoms using the RAG pipeline.

    This endpoint:
    1. Detects language (Chinese/English)
    2. Optionally translates Chinese queries
    3. Retrieves relevant medical information
    4. Generates a response with severity assessment
    5. Returns watch-optimized summary + full response

    Use `?platform=watch` for concise responses optimized for small screens.
    """
    try:
        # Import core modules
        from src.retriever import retrieve_with_fallback, format_context
        from src.llm import (
            get_response,
            build_messages,
            translate_to_english,
            rewrite_query_with_context
        )
        from src.prompts import get_prompt

        # Detect language
        language = request.language
        if language == "auto":
            language = detect_language(request.query)

        # Prepare query
        query = request.query

        # Handle conversation context for follow-up questions
        if request.history and len(request.history) > 0:
            query = await asyncio.to_thread(
                rewrite_query_with_context,
                query,
                request.history
            )

        # Translate Chinese queries for better retrieval
        retrieval_query = query
        if language == "zh":
            retrieval_query = await asyncio.to_thread(
                translate_to_english,
                query
            )

        # Retrieve relevant documents
        results = await asyncio.to_thread(
            retrieve_with_fallback,
            retrieval_query,
            "medquad_symptoms"
        )

        # Format context for LLM
        context = format_context(results)

        # Build messages with appropriate prompt
        # Use watch-optimized prompt when platform is "watch"
        if platform == "watch":
            system_prompt = get_prompt("symptoms", platform="watch")
        else:
            system_prompt = get_prompt("symptoms")
        messages = build_messages(
            system_prompt,
            request.query,  # Use original query for response
            context,
            request.history or []
        )

        # Get LLM response
        full_response = await asyncio.to_thread(
            get_response,
            messages
        )

        # Extract severity and action
        severity, action = extract_severity(full_response)

        # Create watch summary
        summary = create_watch_summary(full_response, severity, action)

        # Prepare sources
        sources = None
        if results.get("metadatas"):
            sources = [
                {
                    "source": meta.get("source", "Unknown"),
                    "category": meta.get("category", ""),
                    "relevance": round((50 - dist) / 30 * 100, 1) if dist else 0
                }
                for meta, dist in zip(
                    results.get("metadatas", [[]]),
                    results.get("distances", [[]])
                )
            ]

        return SymptomResponse(
            success=True,
            summary=summary,
            full_response=full_response,
            confidence=results.get("confidence", 0.5),
            confidence_level=results.get("confidence_level", "medium"),
            sources_count=len(results.get("documents", [[]])[0]) if results.get("documents") else 0,
            sources=sources,
            language_detected=language
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "SYMPTOM_ANALYSIS_ERROR"
            }
        )
