"""API routers for MedBot endpoints."""

from .symptoms import router as symptoms_router
from .medication import router as medication_router
from .records import router as records_router
from .doctors import router as doctors_router
from .clinics import router as clinics_router
from .health import router as health_router

__all__ = [
    "symptoms_router",
    "medication_router",
    "records_router",
    "doctors_router",
    "clinics_router",
    "health_router",
]
