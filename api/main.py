"""
MedBot REST API - FastAPI Entry Point

This module provides REST API endpoints for the MedBot medical assistant,
optimized for Apple Watch and iOS companion app integration.

Usage:
    uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

Or use the launcher:
    python run_api.py
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure src module is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routers import (
    symptoms_router,
    medication_router,
    records_router,
    doctors_router,
    clinics_router,
    health_router,
)
from api.models import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Startup: Pre-load heavy models for faster first request
    Shutdown: Clean up resources
    """
    # Startup: Pre-load models
    print("Starting MedBot API server...")

    try:
        # Pre-load embedding model (takes a few seconds on first load)
        from src.embeddings import get_model
        print("Loading embedding model...")
        get_model()
        print("Embedding model loaded.")

        # Pre-load ChromaDB client
        from src.retriever import get_client
        print("Connecting to vector store...")
        client = get_client()
        collections = client.list_collections()
        print(f"Connected to vector store with {len(collections)} collections.")

    except Exception as e:
        print(f"Warning: Failed to pre-load models: {e}")
        print("Models will be loaded on first request.")

    yield

    # Shutdown
    print("Shutting down MedBot API server...")


# Create FastAPI app
app = FastAPI(
    title="MedBot API",
    description="""
    MedBot REST API for Apple Watch and iOS Integration.

    ## Features

    - **Symptom Analysis**: RAG-powered symptom consultation with severity assessment
    - **Medication Lookup**: Drug information including dosage, interactions, warnings
    - **Records Analysis**: Plain-language interpretation of lab results and diagnoses
    - **Doctor Search**: Find doctors by specialty, language, or name
    - **Clinic Search**: Find nearby clinics by postal code or area

    ## Watch Optimization

    All endpoints return a `summary` object optimized for Apple Watch display:
    - `short`: 50-character summary
    - `severity`: low/medium/high/emergency
    - `action`: self_care/see_doctor/emergency/info
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions with structured error response."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error=str(exc),
            error_code="INTERNAL_SERVER_ERROR",
            details={"path": str(request.url)}
        ).model_dump()
    )


# Include routers with /api/v1 prefix
API_V1_PREFIX = "/api/v1"

app.include_router(health_router, prefix=API_V1_PREFIX)
app.include_router(symptoms_router, prefix=API_V1_PREFIX)
app.include_router(medication_router, prefix=API_V1_PREFIX)
app.include_router(records_router, prefix=API_V1_PREFIX)
app.include_router(doctors_router, prefix=API_V1_PREFIX)
app.include_router(clinics_router, prefix=API_V1_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MedBot API",
        "version": "1.0.0",
        "description": "Medical Assistant REST API for Apple Watch Integration",
        "documentation": "/docs",
        "health_check": "/api/v1/health",
        "endpoints": {
            "symptoms": "/api/v1/symptoms/analyze",
            "medication": "/api/v1/medication/lookup",
            "records": "/api/v1/records/analyze",
            "doctors": "/api/v1/doctors/search",
            "clinics": "/api/v1/clinics/search",
        }
    }
