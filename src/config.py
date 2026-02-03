"""
Configuration constants for MedBot.

This file centralizes all configuration values to ensure consistency
across modules. Import from here instead of hardcoding values.
"""

import os
from pathlib import Path

# =============================================================================
# Path Configuration
# =============================================================================

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Vector store
VECTORSTORE_PATH = PROJECT_ROOT / "vectorstore"

# =============================================================================
# Collection Configuration
# =============================================================================

# ChromaDB collection names mapped to features
COLLECTIONS = {
    "symptoms": "medquad_symptoms",
    "medication": "fda_drugs",
    "records": "medical_records",
    "pubmedqa": "pubmedqa",
    "medqa": "medqa"
}

# Processed data files mapped to collections
DATA_FILES = {
    "medquad_symptoms": PROCESSED_DATA_DIR / "symptoms.jsonl",
    "fda_drugs": PROCESSED_DATA_DIR / "medications.jsonl",
    "medical_records": PROCESSED_DATA_DIR / "records.jsonl",
    "pubmedqa": PROCESSED_DATA_DIR / "pubmedqa.jsonl",
    "medqa": PROCESSED_DATA_DIR / "medqa.jsonl"
}

# All searchable collections for fallback
ALL_COLLECTIONS = ["medquad_symptoms", "fda_drugs", "medical_records", "pubmedqa", "medqa"]

# =============================================================================
# Embedding Configuration
# =============================================================================

# Medical-specialized embedding model (PubMedBERT fine-tuned on MS-MARCO)
# Provides better semantic understanding of medical terminology
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "pritamdeka/S-PubMedBert-MS-MARCO")
EMBEDDING_DIM = 768

# =============================================================================
# Retrieval Configuration
# =============================================================================

DEFAULT_TOP_K = int(os.getenv("TOP_K_RESULTS", "8"))
MAX_CONTEXT_LENGTH = 4000

# Hybrid search weights (BM25 + Dense)
BM25_WEIGHT = 0.3
DENSE_WEIGHT = 0.7
RRF_K = 60  # Reciprocal Rank Fusion constant

# =============================================================================
# Data Processing Configuration
# =============================================================================

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MIN_CONTENT_LENGTH = 50
MAX_CONTENT_LENGTH = 2000
USE_SENTENCE_BOUNDARY = True  # Split at sentence boundaries

# =============================================================================
# Confidence Thresholds
# =============================================================================

# 调整阈值以优化常见症状的检索体验
# - CONFIDENCE_HIGH: 0.7 -> 0.75 (高置信度门槛略微提高)
# - CONFIDENCE_MEDIUM: 0.4 -> 0.55 (让 56% 的结果也触发 fallback)
# - CONFIDENCE_LOW: 0.2 -> 0.3 (低置信度门槛略微提高)
CONFIDENCE_HIGH = 0.75
CONFIDENCE_MEDIUM = 0.55
CONFIDENCE_LOW = 0.3

# Enable cross-collection fallback when confidence is low
ENABLE_CROSS_COLLECTION_FALLBACK = True

# =============================================================================
# LLM Configuration
# =============================================================================

# LLM Provider: "openai" or "deepseek"
# OpenAI is used by default if OPENAI_API_KEY is set
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# OpenAI Configuration
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2-chat-latest")

# DeepSeek Configuration (fallback)
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# Common LLM settings
MAX_TOKENS = 1024
TEMPERATURE = 0.7

# =============================================================================
# Data Source URLs
# =============================================================================

DATA_SOURCES = {
    "medquad": {
        "name": "MedQuAD",
        "url": "https://github.com/abachaa/MedQuAD",
        "description": "Medical Question Answering Dataset from NIH"
    },
    "fda": {
        "name": "OpenFDA",
        "url": "https://api.fda.gov/drug/label.json",
        "description": "FDA Drug Label API"
    },
    "mtsamples": {
        "name": "MTSamples",
        "url": "https://mtsamples.com/",
        "description": "Medical Transcription Samples"
    },
    "pubmedqa": {
        "name": "PubMedQA",
        "url": "https://huggingface.co/datasets/qiaojin/PubMedQA",
        "description": "Biomedical Research QA from PubMed abstracts (~273K)"
    },
    "medqa": {
        "name": "MedQA",
        "url": "https://huggingface.co/datasets/bigbio/med_qa",
        "description": "USMLE Medical Exam Questions (~61K)"
    }
}

# =============================================================================
# Validation
# =============================================================================

VALID_SOURCES = ["MedQuAD", "FDA", "MTSamples", "PubMedQA", "MedQA"]
VALID_CATEGORIES = ["Symptoms", "Diagnosis", "Treatment", "Medication", "Record"]
