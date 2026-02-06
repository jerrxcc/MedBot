"""Health check endpoint for service monitoring."""

import sys
from pathlib import Path
from fastapi import APIRouter

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check the health status of the API and its dependencies.

    Returns service status for:
    - vectorstore: ChromaDB connection
    - llm: LLM API availability
    - embeddings: Embedding model loaded
    """
    services = {}
    overall_status = "healthy"

    # Check vectorstore
    try:
        from src.retriever import get_client
        client = get_client()
        collections = client.list_collections()
        services["vectorstore"] = {
            "status": "healthy",
            "collections_count": len(collections)
        }
    except Exception as e:
        services["vectorstore"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "degraded"

    # Check LLM API configuration
    try:
        from src.llm import is_api_configured
        if is_api_configured():
            services["llm"] = {"status": "healthy"}
        else:
            services["llm"] = {
                "status": "unhealthy",
                "error": "API key not configured"
            }
            overall_status = "degraded"
    except Exception as e:
        services["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "degraded"

    # Check embeddings model
    try:
        from src.embeddings import get_model
        model = get_model()
        services["embeddings"] = {
            "status": "healthy",
            "model": "S-PubMedBERT"
        }
    except Exception as e:
        services["embeddings"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        services=services
    )
