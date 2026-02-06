"""Medical records analysis endpoint using RAG pipeline."""

import sys
import re
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models import RecordsRequest, RecordsResponse, WatchSummary

router = APIRouter(prefix="/records", tags=["Records"])


def detect_language(text: str) -> str:
    """Detect if text is Chinese or English."""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return "zh" if chinese_chars > len(text) * 0.1 else "en"


def extract_abnormal_values(response: str) -> list[str]:
    """Extract mentions of abnormal values from the response."""
    abnormal = []

    # Patterns for abnormal values
    patterns = [
        r'(?:elevated|high|low|abnormal|above|below)[:\s]+([^,.\n]+)',
        r'([A-Za-z0-9\s]+)(?:\s+is|\s+are)?\s+(?:elevated|high|low|abnormal)',
        r'(?:abnormal|concerning|out of range)[:\s]*([^,.\n]+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, response, re.IGNORECASE)
        for match in matches:
            value = match.strip()
            if len(value) > 3 and len(value) < 100:
                abnormal.append(value)

    # Deduplicate and limit
    seen = set()
    unique = []
    for item in abnormal:
        item_lower = item.lower()
        if item_lower not in seen:
            seen.add(item_lower)
            unique.append(item)

    return unique[:10]


def extract_severity_from_records(response: str) -> tuple[str, str]:
    """Extract severity level from medical records analysis."""
    response_lower = response.lower()

    # Critical indicators
    critical_keywords = [
        "critical", "dangerous", "emergency", "immediate",
        "life-threatening", "urgent", "seek care now",
        "危险", "紧急", "立即"
    ]
    for keyword in critical_keywords:
        if keyword in response_lower:
            return "emergency", "emergency"

    # Abnormal indicators
    abnormal_keywords = [
        "abnormal", "elevated", "high", "low", "concerning",
        "follow up", "consult", "doctor", "further testing",
        "异常", "偏高", "偏低"
    ]
    abnormal_count = sum(1 for kw in abnormal_keywords if kw in response_lower)
    if abnormal_count >= 3:
        return "high", "see_doctor"
    elif abnormal_count >= 1:
        return "medium", "self_care"

    return "low", "info"


def create_watch_summary(response: str, severity: str, action: str) -> WatchSummary:
    """Create a watch-optimized summary for records analysis."""
    sentences = re.split(r'[.!?。！？]', response)
    short_text = ""

    # Look for summary-like sentences
    summary_keywords = ["overall", "summary", "conclusion", "in summary", "results show"]
    for sentence in sentences:
        sentence = sentence.strip()
        if any(kw in sentence.lower() for kw in summary_keywords) and len(sentence) > 10:
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
            short_text = sentence if sentence else "Records analyzed."

    return WatchSummary(
        short=short_text or "Records analyzed.",
        severity=severity,
        action=action
    )


@router.post("/analyze", response_model=RecordsResponse)
async def analyze_records(request: RecordsRequest) -> RecordsResponse:
    """
    Analyze medical records and provide interpretation.

    This endpoint:
    1. Parses lab results, diagnoses, or prescriptions
    2. Retrieves relevant medical context
    3. Generates plain-language interpretation
    4. Identifies abnormal values
    5. Returns watch-optimized summary + full analysis
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
            language = detect_language(request.content)

        # Prepare query (the medical record content)
        content = request.content

        # Translate Chinese content for better retrieval
        retrieval_query = content
        if language == "zh":
            retrieval_query = await asyncio.to_thread(
                translate_to_english,
                content
            )

        # Retrieve from medical records collection
        results = await asyncio.to_thread(
            retrieve_with_fallback,
            retrieval_query,
            "medical_records"
        )

        # Format context for LLM
        context = format_context(results)

        # Build messages with records prompt
        system_prompt = get_prompt("records")

        # Enhance prompt based on record type
        if request.record_type == "lab":
            enhanced_content = f"Please analyze these lab results:\n\n{content}"
        elif request.record_type == "diagnosis":
            enhanced_content = f"Please explain this diagnosis:\n\n{content}"
        elif request.record_type == "prescription":
            enhanced_content = f"Please explain this prescription:\n\n{content}"
        else:
            enhanced_content = f"Please analyze this medical record:\n\n{content}"

        messages = build_messages(
            system_prompt,
            enhanced_content,
            context,
            []
        )

        # Get LLM response
        full_response = await asyncio.to_thread(
            get_response,
            messages
        )

        # Extract abnormal values
        abnormal_values = extract_abnormal_values(full_response)

        # Determine severity
        severity, action = extract_severity_from_records(full_response)

        # Create watch summary
        summary = create_watch_summary(full_response, severity, action)

        return RecordsResponse(
            success=True,
            summary=summary,
            full_response=full_response,
            abnormal_values=abnormal_values if abnormal_values else None,
            confidence=results.get("confidence", 0.5),
            confidence_level=results.get("confidence_level", "medium"),
            sources_count=len(results.get("documents", [[]])[0]) if results.get("documents") else 0
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "RECORDS_ANALYSIS_ERROR"
            }
        )
