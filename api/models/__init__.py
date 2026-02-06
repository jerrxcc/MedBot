"""Pydantic models for API requests and responses."""

from .requests import (
    SymptomRequest,
    MedicationRequest,
    RecordsRequest,
    DoctorSearchRequest,
    ClinicSearchRequest,
)
from .responses import (
    WatchSummary,
    SymptomResponse,
    MedicationResponse,
    RecordsResponse,
    DoctorResult,
    DoctorSearchResponse,
    ClinicResult,
    ClinicSearchResponse,
    HealthResponse,
    ErrorResponse,
)

__all__ = [
    "SymptomRequest",
    "MedicationRequest",
    "RecordsRequest",
    "DoctorSearchRequest",
    "ClinicSearchRequest",
    "WatchSummary",
    "SymptomResponse",
    "MedicationResponse",
    "RecordsResponse",
    "DoctorResult",
    "DoctorSearchResponse",
    "ClinicResult",
    "ClinicSearchResponse",
    "HealthResponse",
    "ErrorResponse",
]
