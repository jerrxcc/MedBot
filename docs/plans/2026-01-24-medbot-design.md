# MedBot - AI Medical Assistant Design Document

**Date:** 2026-01-24
**Project:** Deep Learning with Python - Final Project
**Team Size:** 2-3 members

## 1. Overview

MedBot is an AI-powered medical assistant that provides:
- **Symptom Consultation** - Analyze symptoms and suggest possible conditions
- **Medication Information** - Drug details, usage, side effects
- **Medical Records Analysis** - Parse and analyze clinical documents

### Tech Stack
| Component | Choice |
|-----------|--------|
| LLM | DeepSeek V3 API |
| Embedding | all-MiniLM-L6-v2 |
| Vector DB | ChromaDB |
| Web Framework | Gradio |
| Notebook | Jupyter |

## 2. Data Sources

- **MedQuAD**: 47,000+ QA pairs from NIH (https://github.com/abachaa/MedQuAD)
- **FDA Drug Labels**: OpenFDA API (https://open.fda.gov)
- **MTSamples**: Medical transcription samples (https://mtsamples.com)

## 3. Team Assignment

### Member A: Data & Embedding
- Download and clean datasets
- Data preprocessing (chunking, formatting)
- Build ChromaDB vector store

### Member B: RAG Backend & LLM
- DeepSeek API integration
- Retrieval logic
- Prompt design

### Member C: Frontend & Demo
- Gradio UI development
- UI styling
- Jupyter Notebook documentation

## 4. Timeline

### Week 1
- Data collection & processing
- API wrapper & prompt design
- Gradio framework setup

### Week 2
- Vector store optimization
- Three-feature logic refinement
- UI polish & Notebook docs
