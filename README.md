# MedBot - AI Medical Assistant (RAG)

MedBot is a Retrieval-Augmented Generation (RAG) medical information assistant. It supports symptom Q&A, medication information, plus Singapore-specific doctor and clinic search.

**Project Type:** Deep Learning with Python - Final Project  
**Team:** C. Cai | Y. Liao | D. Liu | Y. Qian | X. Wang | Y. Wang

## Features

| Feature | What it does | Entry points |
|---|---|---|
| Symptom analysis | Retrieves medical Q&A context and generates guidance | Chainlit / Gradio / CLI |
| Medication info | Uses FDA label data for usage, side effects, interactions | Chainlit / Gradio / CLI |
| Find doctor (Singapore) | Searches `Specialists.xlsx` by specialty/language/name | Chainlit / Gradio / CLI |
| Find clinic (Singapore) | Searches `Clinics.xlsx` by postal code/area/name with a distance heuristic | Chainlit / CLI |

Note: The Gradio UI includes the Doctor search tab, but does not include the Clinic search mode. Clinic search is available in Chainlit and the CLI.

## Quick Start

### 1. Install Dependencies

macOS/Linux:

```bash
bash setup.sh
```

Windows:

```bat
setup.bat
```

These scripts:

- Create a `venv/`
- Install `requirements.txt`
- Create `.env` from `.env.example` (if missing)
- Optionally download datasets and build the vector store (interactive prompt)

### 2. Configure API Key

MedBot requires an OpenAI or DeepSeek API key. The key is used for response generation and also for:

- Chinese -> English retrieval keyword translation (`src/translator.py`)
- Context-aware query rewriting for follow-up questions (`src/llm.py`)

```bash
cp .env.example .env
```

Then set at least one of:

```dotenv
OPENAI_API_KEY=...
# or
DEEPSEEK_API_KEY=...
```

### 3. Run

Chainlit (recommended, port 8000):

```bash
# Activate the virtual environment (if created by setup scripts)
source venv/bin/activate  # Windows: venv\Scripts\activate
./run.sh
# Windows: run.bat
```

Open `http://localhost:8000`.

Gradio (classic UI, port 7860):

```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
python3 app.py
```

CLI (developer / regression tool):

```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
python3 cli.py
```

Stop Chainlit:

```bash
./stop.sh
```

## Architecture (Matches the Code)

### Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                   UI                                     │
│                                                                          │
│   Chainlit: app_chainlit.py (http://localhost:8000)                      │
│   Gradio:   app.py          (http://localhost:7860)                      │
│   CLI:      cli.py          (python3 cli.py)                             │
└───────────────────────────────┬───────────────────────────────┬──────────┘
                                │                               │
                                │ RAG modes                     │ Search modes
                                │ (symptoms/medication)         │ (doctors/clinics)
                                ▼                               ▼
┌──────────────────────────────────────────────────┐   ┌───────────────────────────────┐
│ Query Prep (optional / best-effort)              │   │ Intent Parsing (LLM JSON plan)│
│  - Follow-up rewrite: src/llm.py                 │   └───────────────┬───────────────┘
│  - zh -> en keywords: src/translator.py          │                   │
└───────────────────────────────┬──────────────────┘                   │
                                │                                      │
                                ▼                                      ▼
┌──────────────────────────────────────────────────────────────────┐   ┌───────────────────────────────┐
│ Retrieval: ChromaDB PersistentClient (vectorstore/)              │   │ Search Agents                 │
│  - Primary collection by mode                                    │   │  - MedicalSearchAgent         │
│  - Confidence scoring (distances -> level)                       │   │  - ClinicSearchAgent          │
│  - Low-confidence cross-collection fallback (ALL_COLLECTIONS)    │   │ Data: Specialists.xlsx        │
│                                                                  │   │       Clinics.xlsx            │
└───────────────────────────────┬──────────────────────────────────┘   └───────────────┬───────────────┘
                                │                                      │
                                ▼                                      │
┌──────────────────────────────────────────────────┐                   │
│ Context Formatting: src/retriever.py             │                   │
└───────────────────────────────┬──────────────────┘                   │
                                │                                      │
                                ▼                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LLM Response: src/llm.py (OpenAI / DeepSeek, OpenAI-compatible client)   │
└──────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                           Final Response
```

Note:
- Default retrieval used by UIs is `src/retriever.py` (dense retrieval + confidence scoring + cross-collection fallback).
- `src/hybrid_retriever.py` is **experimental** (BM25 + dense + RRF). It is kept for offline experiments and is not wired into the UIs.

## Data and Vector Store

### Processed Data

Processed data lives in `data/processed/*.jsonl` (JSONL: one `{id, content, metadata}` per line).

To inspect counts locally:

```bash
wc -l data/processed/*.jsonl
```

### Chroma Vector Store

MedBot uses `vectorstore/` for ChromaDB persistent storage. If `vectorstore/` is missing, you can:

Download a prebuilt vector store (GitHub release asset `vectorstore.zip`):

```bash
bash scripts/download_vectorstore.sh
```

Build from scratch (slow: downloads + processes datasets, then embeds and builds collections):

```bash
python3 scripts/download_all.py
python3 scripts/build_vectorstore.py --clear
```

## Datasets / Sources

| Dataset | Used for | Source |
|---|---|---|
| MedQuAD | NIH medical Q&A (symptoms/diagnosis/treatment, etc.) | [abachaa/MedQuAD](https://github.com/abachaa/MedQuAD) |
| OpenFDA Drug Label | Medication labels (usage, warnings, adverse reactions) | [open.fda.gov](https://open.fda.gov) |
| MTSamples | Medical record/transcription samples (dataset; UI mode removed) | [mtsamples.com](https://mtsamples.com) |
| PubMedQA | Biomedical Q&A (can be hit by fallback retrieval) | [qiaojin/PubMedQA](https://huggingface.co/datasets/qiaojin/PubMedQA) |
| MedQA | USMLE-style medical Q&A (can be hit by fallback retrieval) | [bigbio/med_qa](https://huggingface.co/datasets/bigbio/med_qa) |

## Configuration

Common environment variables (put them in `.env`):

| Variable | Meaning | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI key | - |
| `OPENAI_BASE_URL` | OpenAI base URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | OpenAI model name | `gpt-5.2-2025-12-11` |
| `DEEPSEEK_API_KEY` | DeepSeek key | - |
| `DEEPSEEK_BASE_URL` | DeepSeek base URL | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | DeepSeek model name | `deepseek-chat` |
| `EMBEDDING_MODEL` | SentenceTransformer embedding model | `pritamdeka/S-PubMedBert-MS-MARCO` |
| `TOP_K_RESULTS` | Chainlit retrieval top_k | `8` |

Code-level toggles (see `src/config.py`):

| Setting | Meaning |
|---|---|
| `ENABLE_CROSS_COLLECTION_FALLBACK` | Search multiple collections when confidence is low |
| `ENABLE_CONTEXT_AWARE_RETRIEVAL` | Rewrite short follow-ups using conversation context |

## Project Structure

```
MED_BOT/
├── app_chainlit.py               # Chainlit UI (recommended)
├── app.py                        # Gradio UI (classic)
├── cli.py                        # CLI (developer / regression tool)
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── Clinics.xlsx                  # Clinic dataset (Singapore)
├── Specialists.xlsx              # Specialist/doctor dataset (Singapore)
│
├── src/
│   ├── config.py                 # Global config + paths + collection names
│   ├── llm.py                    # OpenAI-compatible client wrapper (OpenAI/DeepSeek)
│   ├── prompts.py                # System prompts
│   ├── embeddings.py             # SentenceTransformer embeddings + cache
│   ├── retriever.py              # Chroma retrieval + confidence + fallback
│   ├── translator.py             # Chinese -> English retrieval translation (LLM)
│   ├── hybrid_retriever.py       # (experimental) BM25 + Dense + RRF
│   ├── search_agent.py           # Doctor search (LLM intent + Excel search)
│   ├── clinic_search.py          # Clinic search (LLM intent + postal/area)
│   ├── location.py               # Postal distance heuristic + nearby-area mapping
│   └── cli/                      # CLI implementation
│
├── scripts/
│   ├── download_all.py           # Download and process all datasets
│   ├── download_vectorstore.sh   # Download prebuilt vectorstore
│   └── build_vectorstore.py      # Build Chroma collections
│
├── data/
│   ├── raw/
│   └── processed/
│
├── vectorstore/                  # ChromaDB persistent storage
└── tests/
```

## Testing

Minimal regression entry point (mainly ensures CLI runs end-to-end, not strict output checks):

```bash
make check
```

## Troubleshooting

### API key missing

Ensure `.env` exists in the project root and sets at least one:

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`

### Port already in use

Prefer:

```bash
./stop.sh
```

Or manually (macOS/Linux):

```bash
lsof -ti:8000 | xargs kill -9
lsof -ti:7860 | xargs kill -9
```

### First run is slow

The first run downloads and loads the SentenceTransformer `EMBEDDING_MODEL`, which can take time and memory.

## Disclaimer

For educational purposes only. This is not medical advice. Always consult a qualified healthcare professional.

## License

This is an academic/learning project. Datasets and models are subject to their respective licenses and terms.
