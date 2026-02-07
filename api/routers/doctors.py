"""Doctor search endpoint using the search agent."""

import sys
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models import (
    DoctorSearchRequest,
    DoctorSearchResponse,
    DoctorResult,
    WatchSummary
)

router = APIRouter(prefix="/doctors", tags=["Doctors"])


import re


def _strip_md(text: str) -> str:
    """Remove markdown bold/italic markers and leading list dashes."""
    return text.replace('**', '').replace('*', '').strip().lstrip('-').strip()


def parse_doctor_results(markdown_response: str) -> list[dict]:
    """Parse markdown doctor results into structured data.

    Expected format from search_agent._format_results:
        ### Found N Matching Doctors
        #### 1. Dr. Name
        - **Specialty:** ...
        - **Languages:** ...
        ---
    """
    doctors = []
    current_doctor = {}

    for line in markdown_response.split('\n'):
        line = line.strip()

        # Skip empty lines, separators, and the summary header
        if not line or line == '---':
            continue
        if re.match(r'^#{1,4}\s*Found\s+\d+', line):
            continue

        # Doctor name line: #### 1. Dr. Name  or  ### 1. Dr. Name
        name_match = re.match(r'^#{1,4}\s*\d+\.\s*(.+)', line)
        if name_match:
            if current_doctor.get('name'):
                doctors.append(current_doctor)
            current_doctor = {'name': _strip_md(name_match.group(1))}
            continue

        # Key-value line: - **Specialty:** Cardiology
        if ':' in line and current_doctor:
            key, value = line.split(':', 1)
            key = _strip_md(key).lower()
            value = _strip_md(value)

            if 'specialty' in key or 'speciality' in key:
                current_doctor['specialty'] = value
            elif 'language' in key:
                current_doctor['languages'] = [
                    lang.strip() for lang in value.split(',')
                ]
            elif 'designation' in key or 'title' in key:
                current_doctor['designation'] = value
            elif 'clinic' in key:
                current_doctor['clinic_name'] = value
            elif 'contact' in key or 'phone' in key:
                current_doctor['contact'] = value
            elif 'service' in key:
                current_doctor['services'] = value

    if current_doctor.get('name'):
        doctors.append(current_doctor)

    return doctors


def create_watch_summary(doctors: list[dict], total: int) -> WatchSummary:
    """Create watch-optimized summary for doctor search."""
    if total == 0:
        return WatchSummary(
            short="No doctors found matching criteria",
            severity="low",
            action="info"
        )
    elif total == 1:
        doc = doctors[0]
        short = f"Found: {doc.get('name', 'Doctor')}"
        if len(short) > 47:
            short = short[:47] + "..."
        return WatchSummary(
            short=short,
            severity="low",
            action="info"
        )
    else:
        return WatchSummary(
            short=f"Found {total} matching doctors",
            severity="low",
            action="info"
        )


@router.post("/search", response_model=DoctorSearchResponse)
async def search_doctors(request: DoctorSearchRequest) -> DoctorSearchResponse:
    """
    Search for doctors by specialty, language, or name.

    This endpoint uses natural language processing to understand
    search intent and returns matching doctors with relevance scoring.
    """
    try:
        # Import search agent
        from src.search_agent import MedicalSearchAgent

        # Initialize agent
        agent = MedicalSearchAgent()

        # Build search query
        query = request.query

        # Add explicit filters if provided
        if request.specialty and request.specialty.lower() not in query.lower():
            query = f"{query} specialty: {request.specialty}"
        if request.language and request.language.lower() not in query.lower():
            query = f"{query} speaks {request.language}"
        if request.name and request.name.lower() not in query.lower():
            query = f"{query} name: {request.name}"

        # Perform search – agent.search() returns a single markdown string
        result_markdown = await asyncio.to_thread(
            agent.search,
            query
        )
        plan = None

        # Parse results
        parsed_doctors = parse_doctor_results(result_markdown)

        # Convert to response models
        doctor_results = []
        for doc in parsed_doctors[:request.limit]:
            doctor_results.append(DoctorResult(
                name=doc.get('name', 'Unknown'),
                specialty=doc.get('specialty', 'General'),
                languages=doc.get('languages', ['English']),
                designation=doc.get('designation'),
                clinic_name=doc.get('clinic_name'),
                contact=doc.get('contact'),
                match_score=doc.get('score')
            ))

        # Create summary
        summary = create_watch_summary(doctor_results, len(doctor_results))

        return DoctorSearchResponse(
            success=True,
            summary=summary,
            results=doctor_results,
            total_count=len(doctor_results),
            search_plan=plan
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "DOCTOR_SEARCH_ERROR"
            }
        )
