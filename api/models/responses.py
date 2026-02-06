"""Pydantic response models for API endpoints."""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class WatchSummary(BaseModel):
    """Watch-optimized summary for small screen display."""

    short: str = Field(
        ...,
        max_length=50,
        description="50 chars max for watch display"
    )
    severity: Literal["low", "medium", "high", "emergency"] = Field(
        ...,
        description="Severity level for visual indication"
    )
    action: Literal["self_care", "see_doctor", "emergency", "info"] = Field(
        ...,
        description="Recommended action"
    )


class SymptomResponse(BaseModel):
    """Response model for symptom analysis."""

    success: bool = True
    summary: WatchSummary = Field(
        ...,
        description="Watch-optimized summary"
    )
    full_response: str = Field(
        ...,
        description="Complete response for iOS app"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    confidence_level: Literal["high", "medium", "low", "very_low"] = Field(
        ...,
        description="Confidence level category"
    )
    sources_count: int = Field(
        ...,
        ge=0,
        description="Number of sources used"
    )
    sources: Optional[List[dict]] = Field(
        default=None,
        description="Source documents (for iOS full view)"
    )
    language_detected: str = Field(
        default="en",
        description="Detected language of input"
    )


class MedicationResponse(BaseModel):
    """Response model for medication lookup."""

    success: bool = True
    summary: WatchSummary = Field(
        ...,
        description="Watch-optimized summary"
    )
    full_response: str = Field(
        ...,
        description="Complete medication information"
    )
    drug_name: Optional[str] = Field(
        default=None,
        description="Identified drug name"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )
    confidence_level: str
    sources_count: int
    warnings: Optional[List[str]] = Field(
        default=None,
        description="Important warnings extracted"
    )


class RecordsResponse(BaseModel):
    """Response model for medical records analysis."""

    success: bool = True
    summary: WatchSummary = Field(
        ...,
        description="Watch-optimized summary"
    )
    full_response: str = Field(
        ...,
        description="Complete interpretation"
    )
    abnormal_values: Optional[List[str]] = Field(
        default=None,
        description="List of abnormal values found"
    )
    confidence: float
    confidence_level: str
    sources_count: int


class DoctorResult(BaseModel):
    """Individual doctor result."""

    name: str = Field(..., description="Doctor's name")
    specialty: str = Field(..., description="Medical specialty")
    languages: List[str] = Field(..., description="Languages spoken")
    designation: Optional[str] = Field(default=None, description="Title/designation")
    clinic_name: Optional[str] = Field(default=None, description="Clinic affiliation")
    contact: Optional[str] = Field(default=None, description="Contact information")
    match_score: Optional[float] = Field(default=None, description="Search relevance score")


class DoctorSearchResponse(BaseModel):
    """Response model for doctor search."""

    success: bool = True
    summary: WatchSummary = Field(
        ...,
        description="Watch-optimized summary"
    )
    results: List[DoctorResult] = Field(
        ...,
        description="List of matching doctors"
    )
    total_count: int = Field(
        ...,
        description="Total number of matches"
    )
    search_plan: Optional[dict] = Field(
        default=None,
        description="Search plan details for debugging"
    )


class ClinicResult(BaseModel):
    """Individual clinic result."""

    name: str = Field(..., description="Clinic name")
    address: str = Field(..., description="Full address")
    area: str = Field(..., description="Singapore area")
    contact: Optional[str] = Field(default=None, description="Contact number")
    distance_meters: Optional[int] = Field(default=None, description="Distance from search location")
    postal_code: Optional[str] = Field(default=None, description="Postal code")
    from_nearby_area: Optional[str] = Field(default=None, description="If from nearby area fallback")


class ClinicSearchResponse(BaseModel):
    """Response model for clinic search."""

    success: bool = True
    summary: WatchSummary = Field(
        ...,
        description="Watch-optimized summary"
    )
    results: List[ClinicResult] = Field(
        ...,
        description="List of matching clinics"
    )
    total_count: int = Field(
        ...,
        description="Total number of matches"
    )
    search_plan: Optional[dict] = Field(
        default=None,
        description="Search plan details"
    )
    map_available: bool = Field(
        default=False,
        description="Whether map HTML is available"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    version: str = "1.0.0"
    services: dict = Field(
        default_factory=dict,
        description="Individual service statuses"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")
    details: Optional[dict] = Field(default=None, description="Additional error details")
