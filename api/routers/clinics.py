"""Clinic search endpoint using the clinic search agent."""

import sys
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models import (
    ClinicSearchRequest,
    ClinicSearchResponse,
    ClinicResult,
    WatchSummary
)

router = APIRouter(prefix="/clinics", tags=["Clinics"])


def create_watch_summary(clinics: list, total: int) -> WatchSummary:
    """Create watch-optimized summary for clinic search."""
    if total == 0:
        return WatchSummary(
            short="No clinics found nearby",
            severity="low",
            action="info"
        )
    elif total == 1:
        clinic = clinics[0]
        name = clinic.name if hasattr(clinic, 'name') else clinic.get('name', 'Clinic')
        short = f"Found: {name}"
        if len(short) > 47:
            short = short[:47] + "..."
        return WatchSummary(
            short=short,
            severity="low",
            action="info"
        )
    else:
        return WatchSummary(
            short=f"Found {total} clinics nearby",
            severity="low",
            action="info"
        )


@router.post("/search", response_model=ClinicSearchResponse)
async def search_clinics(request: ClinicSearchRequest) -> ClinicSearchResponse:
    """
    Search for clinics by postal code, area, or name.

    This endpoint supports:
    - Distance-based search by Singapore postal code
    - Area-based search with nearby area fallback
    - Name-based fuzzy matching
    - Natural language queries
    """
    try:
        # Import clinic search agent
        from src.clinic_search import ClinicSearchAgent

        # Initialize agent
        agent = ClinicSearchAgent()

        # Build search query
        query = request.query

        # Add explicit filters if provided
        if request.postal_code and request.postal_code not in query:
            query = f"{query} near postal code {request.postal_code}"
        if request.area and request.area.lower() not in query.lower():
            query = f"{query} in {request.area}"
        if request.clinic_name and request.clinic_name.lower() not in query.lower():
            query = f"{query} named {request.clinic_name}"

        # Perform search – agent.search() returns (results, plan)
        results, plan = await asyncio.to_thread(
            agent.search,
            query
        )
        map_html = None

        # Convert to response models
        clinic_results = []
        for clinic in results[:request.limit]:
            clinic_results.append(ClinicResult(
                name=clinic.get('Name', 'Unknown Clinic'),
                address=clinic.get('Address', ''),
                area=clinic.get('Area', ''),
                contact=clinic.get('Contact'),
                distance_meters=clinic.get('_distance'),
                postal_code=clinic.get('Postal Code'),
                from_nearby_area=clinic.get('_from_nearby')
            ))

        # Create summary
        summary = create_watch_summary(clinic_results, len(clinic_results))

        return ClinicSearchResponse(
            success=True,
            summary=summary,
            results=clinic_results,
            total_count=len(clinic_results),
            search_plan=plan,
            map_available=map_html is not None
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "CLINIC_SEARCH_ERROR"
            }
        )
