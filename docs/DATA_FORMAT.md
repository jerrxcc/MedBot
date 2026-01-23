# Data Format Specifications

This document defines the data formats used throughout the MedBot project.

## 1. Directory Structure

```
data/
├── raw/                          # Original downloaded data
│   ├── medquad/                  # MedQuAD dataset
│   ├── fda_drugs/                # FDA drug labels
│   └── mtsamples/                # Medical transcription samples
└── processed/                    # Cleaned, formatted data
    ├── symptoms.jsonl            # Symptom consultation data
    ├── medications.jsonl         # Medication information
    └── records.jsonl             # Medical records samples
```

## 2. Processed Data Format (JSONL)

All processed data files use **JSON Lines** format (`.jsonl`) - one JSON object per line.

### 2.1 Symptoms Data (`symptoms.jsonl`)

```json
{
  "id": "medquad_001",
  "content": "Question: What are diabetes symptoms?\n\nAnswer: Common symptoms include...",
  "metadata": {
    "source": "MedQuAD",
    "category": "Symptoms",
    "condition": "Diabetes",
    "url": "https://www.nlm.nih.gov/..."
  }
}
```

### 2.2 Medications Data (`medications.jsonl`)

```json
{
  "id": "fda_001",
  "content": "Drug: Ibuprofen\n\nPurpose: Pain relief...",
  "metadata": {
    "source": "FDA",
    "drug_name": "Ibuprofen",
    "category": "NSAID",
    "usage": "Pain relief, fever reduction",
    "warnings": "May cause stomach bleeding"
  }
}
```

### 2.3 Medical Records Data (`records.jsonl`)

```json
{
  "id": "mtsamples_001",
  "content": "CHIEF COMPLAINT: Chest pain...",
  "metadata": {
    "source": "MTSamples",
    "specialty": "Cardiology",
    "document_type": "Consultation Note",
    "sample_type": "template"
  }
}
```

## 3. Vector Store Collections

| Collection Name | Data File | Description |
|-----------------|-----------|-------------|
| `medquad_symptoms` | `symptoms.jsonl` | Symptom consultation knowledge |
| `fda_drugs` | `medications.jsonl` | Medication information |
| `medical_records` | `records.jsonl` | Medical record templates |

## 4. API Data Formats

### Retriever Output

```python
{
    "documents": ["doc1 content", "doc2 content", ...],
    "metadatas": [{"source": "...", ...}, ...],
    "distances": [0.123, 0.234, ...]  # Lower = more similar
}
```

### LLM Messages Format

```python
messages = [
    {"role": "system", "content": "You are MedBot..."},
    {"role": "user", "content": "### Reference Information:\n{context}\n\n### Question:\n{question}"}
]
```

## 5. Validation Rules

- `id`: Must be unique, format `{source}_{number}`
- `content`: Non-empty, 50-2000 characters recommended
- `metadata.source`: Must be one of: "MedQuAD", "FDA", "MTSamples"
