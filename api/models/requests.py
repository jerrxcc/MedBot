"""Pydantic request models for API endpoints."""

from typing import Optional, List
from pydantic import BaseModel, Field


class SymptomRequest(BaseModel):
    """Request model for symptom analysis."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's symptom description",
        examples=["I have a headache and feel dizzy"]
    )
    language: Optional[str] = Field(
        default="auto",
        description="Language preference: 'en', 'zh', or 'auto' for detection",
        examples=["en", "zh", "auto"]
    )
    history: Optional[List[dict]] = Field(
        default=None,
        description="Previous conversation history for context",
        examples=[[{"role": "user", "content": "I have a headache"}]]
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )


class MedicationRequest(BaseModel):
    """Request model for medication lookup."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Medication name or question",
        examples=["What is the dosage for ibuprofen?"]
    )
    language: Optional[str] = Field(
        default="auto",
        description="Language preference: 'en', 'zh', or 'auto'"
    )
    history: Optional[List[dict]] = Field(
        default=None,
        description="Previous conversation history"
    )


class RecordsRequest(BaseModel):
    """Request model for medical records analysis."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Medical record content (lab results, diagnosis, etc.)",
        examples=["HbA1c: 7.2%, Fasting glucose: 130 mg/dL"]
    )
    language: Optional[str] = Field(
        default="auto",
        description="Language preference: 'en', 'zh', or 'auto'"
    )
    record_type: Optional[str] = Field(
        default="general",
        description="Type of record: 'lab', 'diagnosis', 'prescription', 'general'",
        examples=["lab", "diagnosis"]
    )


class DoctorSearchRequest(BaseModel):
    """Request model for doctor search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query",
        examples=["Find a cardiologist who speaks Mandarin"]
    )
    specialty: Optional[str] = Field(
        default=None,
        description="Filter by specialty",
        examples=["Cardiology", "Dermatology"]
    )
    language: Optional[str] = Field(
        default=None,
        description="Filter by language spoken",
        examples=["Mandarin", "English", "Malay"]
    )
    name: Optional[str] = Field(
        default=None,
        description="Search by doctor name"
    )
    limit: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results"
    )


class ClinicSearchRequest(BaseModel):
    """Request model for clinic search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query",
        examples=["Clinics near postal code 640123"]
    )
    postal_code: Optional[str] = Field(
        default=None,
        description="Singapore postal code for distance-based search",
        examples=["640123", "520123"]
    )
    area: Optional[str] = Field(
        default=None,
        description="Singapore area name",
        examples=["Bedok", "Tampines", "Jurong East"]
    )
    clinic_name: Optional[str] = Field(
        default=None,
        description="Search by clinic name"
    )
    limit: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results"
    )
