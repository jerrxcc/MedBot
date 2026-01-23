# MedBot - AI Medical Assistant

A RAG-based (Retrieval-Augmented Generation) medical assistant powered by deep learning.

**Course:** Deep Learning with Python
**Project Type:** Final Project

---

## Features

| Feature | Description |
|---------|-------------|
| **Symptom Consultation** | Describe symptoms, get possible conditions and advice |
| **Medication Information** | Query drug usage, side effects, interactions |
| **Medical Records Analysis** | Analyze and explain medical documents |

---

## Screenshots

### Chainlit Interface (Recommended)
Modern chat UI similar to ChatGPT with dark/light theme support.

### Gradio Interface
Classic tabbed interface for quick access to different features.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI                               │
│         ┌──────────────┐    ┌──────────────┐               │
│         │   Chainlit   │    │    Gradio    │               │
│         │  (Port 8000) │    │  (Port 7860) │               │
│         └──────┬───────┘    └──────┬───────┘               │
└────────────────┼───────────────────┼────────────────────────┘
                 │                   │
                 └─────────┬─────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     RAG Pipeline                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Embedding  │───▶│  ChromaDB   │───▶│  Retriever  │     │
│  │ (MiniLM-L6) │    │ (Vector DB) │    │  (Top-K)    │     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘     │
└───────────────────────────────────────────────┼─────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    DeepSeek V3 API                          │
│           (Context-aware response generation)               │
└─────────────────────────────────────────────────────────────┘
```

### Deep Learning Components

1. **Sentence Transformers** - BERT-based text embedding model (all-MiniLM-L6-v2)
2. **Vector Similarity Search** - Semantic retrieval using cosine similarity
3. **Large Language Model** - Context-aware response generation via DeepSeek API

---

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/jerrxcc/MedBot.git
cd MedBot

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Chainlit (for modern UI)
pip install chainlit
```

### 2. Configure API Key

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your DeepSeek API key
# DEEPSEEK_API_KEY=your_api_key_here
```

Get your API key at: https://platform.deepseek.com/

### 3. Download and Process Data

```bash
# Download all datasets
python scripts/download_all.py

# Build vector store
python scripts/build_vectorstore.py
```

### 4. Run Application

**Option A: Chainlit (Recommended - Modern UI)**

```bash
chainlit run app_chainlit.py
```

Open http://localhost:8000 in your browser.

**Option B: Gradio (Classic UI)**

```bash
python app.py
```

Open http://localhost:7860 in your browser.

---

## User Interfaces

### Chainlit Interface

Modern, ChatGPT-like interface with:
- Dark/Light theme toggle
- Real-time streaming responses
- Markdown formatting support
- Copy button for responses
- File upload support

**Commands:**
| Command | Description |
|---------|-------------|
| `/help` | Show help message |
| `/zh` | Switch to Chinese responses |
| `/en` | Switch to English responses |

**Mode Switching:** Use the dropdown menu in the top-left corner to switch between Symptom Analysis, Medication Info, and Records Analysis.

### Gradio Interface

Classic tabbed interface with:
- Three separate tabs for each feature
- Example questions for quick start
- API status indicator
- Clear chat button

---

## Project Structure

```
MedBot/
├── app.py                      # Gradio application
├── app_chainlit.py             # Chainlit application (recommended)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── README.md                   # This file
│
├── src/                        # Source code modules
│   ├── __init__.py
│   ├── config.py               # Configuration constants
│   ├── embeddings.py           # Text embedding functions
│   ├── retriever.py            # Vector search & retrieval
│   ├── llm.py                  # DeepSeek API wrapper
│   └── prompts.py              # Prompt templates
│
├── scripts/                    # Data processing scripts
│   ├── download_all.py         # Download all datasets
│   ├── download_medquad.py     # MedQuAD dataset
│   ├── download_fda.py         # FDA drug labels
│   ├── download_mtsamples.py   # Medical records
│   └── build_vectorstore.py    # Build ChromaDB collections
│
├── data/                       # Data storage
│   ├── raw/                    # Original downloaded data
│   └── processed/              # Cleaned JSONL files
│
├── vectorstore/                # ChromaDB persistent storage
│
├── notebooks/
│   └── demo.ipynb              # Technical demonstration
│
└── docs/
    ├── plans/                  # Design documents
    │   └── 2026-01-24-medbot-design.md
    └── DATA_FORMAT.md          # Data format specifications
```

---

## Data Sources

| Dataset | Source | Content |
|---------|--------|---------|
| **MedQuAD** | [GitHub](https://github.com/abachaa/MedQuAD) | 47K+ medical Q&A pairs from NIH |
| **FDA Drug Labels** | [OpenFDA API](https://open.fda.gov) | Drug usage, warnings, side effects |
| **MTSamples** | [Kaggle](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions) | Medical transcription samples |

---

## Troubleshooting

### API Key Issues

If you see "API Key Required" error:
1. Make sure `.env` file exists in project root
2. Check that `DEEPSEEK_API_KEY` is set correctly
3. Restart the application after changing `.env`

### Vector Store Issues

If retrieval doesn't work:
```bash
# Rebuild vector store
python scripts/build_vectorstore.py --clear
```

### Port Already in Use

```bash
# Kill existing process on port
lsof -ti:8000 | xargs kill -9  # For Chainlit
lsof -ti:7860 | xargs kill -9  # For Gradio
```

---

## Disclaimer

This application is for **educational purposes only**. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for medical concerns.

---

## License

This project is for academic use. Data sources retain their original licenses:
- MedQuAD: Public domain (NIH)
- OpenFDA: Public domain (FDA)
- MTSamples: Educational use
