# MedBot CLI User Guide

## Overview

The MedBot CLI provides full command-line access to all MedBot features with automatic intent detection and conversation history. It has the same functionality as the web interfaces (Gradio/Chainlit), just without the visual UI elements.

## Starting the CLI

```bash
python3 cli.py
```

## Features

The CLI supports all 5 core MedBot features:

### 1. Symptom Analysis
Ask about symptoms and get medical information.

**Examples:**
```
medbot> I have a headache and feel dizzy
medbot> persistent cough with chest tightness
medbot> 我头痛 (Chinese supported)
```

### 2. Medication Information
Get information about drugs, dosages, and side effects.

**Examples:**
```
medbot> side effects of aspirin
medbot> what is ibuprofen used for?
medbot> can I take aspirin with blood pressure medication?
```

### 3. Medical Records Analysis
Understand medical reports, lab results, and diagnoses.

**Examples:**
```
medbot> what is diabetes?
medbot> explain hemoglobin level of 10.5
medbot> what is a normal blood pressure?
```

### 4. Doctor Search
Find doctors and specialists in Singapore.

**Examples:**
```
medbot> find a dentist
medbot> looking for a Chinese speaking cardiologist
medbot> find Dr. Tan
```

### 5. Clinic Search
Find nearby clinics in Singapore.

**Examples:**
```
medbot> clinic near 520123
medbot> find clinic in Tampines
medbot> medical center near Orchard
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show usage instructions |
| `/mode <feature>` | Switch to specific mode (auto/symptoms/medication/records/doctors/clinics) |
| `/clear` | Clear conversation history |
| `/status` | Show current mode and API status |
| `/history` | Show recent conversation |
| `/quit` or `/exit` | Exit MedBot CLI |

## Mode Switching

### Auto Mode (Default)
Automatically detects intent from your query.

```
medbot> I have a fever          → Symptoms
medbot> side effects of aspirin → Medication
medbot> find a dentist          → Doctors
```

### Manual Mode
Force a specific feature mode.

```
medbot> /mode medication
Switched to 'medication' mode.
medbot> aspirin                 → [Mode: medication]
```

Return to auto mode:
```
medbot> /mode auto
```

## Conversation Context

The CLI maintains conversation history (last 10 turns) for follow-up questions:

```
medbot> I have a headache
[Response about headaches...]

medbot> what about fever?
[Rewritten query: Headache with fever causes...]
[Response considers both headache and fever...]
```

## Keyboard Shortcuts

- **Ctrl+C** - Cancel current input (continues session)
- **Ctrl+D** - Exit CLI
- **Tab** - Auto-complete slash commands (if supported by terminal)

## Intent Detection

The CLI automatically detects your intent using keywords:

| Intent | Trigger Keywords |
|--------|------------------|
| Symptoms | pain, ache, dizzy, fever, cough, feel, symptom |
| Medication | medicine, drug, pill, side effect, aspirin, ibuprofen |
| Records | disease, diabetes, diagnosis, what is, condition |
| Doctors | doctor, dentist, specialist, cardiologist, find |
| Clinics | clinic, hospital, near, nearby, postal code |

**Priority Rules:**
- "find a" or "looking for" → Doctors
- "near" or "postal code" → Clinics
- "side effect" → Medication

## Configuration

### API Key Setup

The CLI requires an API key. Set one of:

```bash
export OPENAI_API_KEY="your-key-here"
# or
export DEEPSEEK_API_KEY="your-key-here"
```

Or create a `.env` file:
```
DEEPSEEK_API_KEY=your-key-here
```

### Check API Status
```
medbot> /status
Mode: auto
API: openai connected
History: 0 messages
```

## Output Format

### RAG Queries (Symptoms/Medication/Records)

```
[Detected: symptoms]
Searching symptoms knowledge base...
ℹ️  Medium confidence - review results carefully

[AI Response with medical information...]

[Confidence: 75%]
```

### Doctor Search

```
[Detected: doctors]
Loading doctor database...
Searching for doctors...

### Found 5 Matching Doctors

#### 1. Dr. Ng Wee Hsuan
- **Specialty:** Dental
- **Languages:** English, Mandarin
- **Services:** Dental Surgery
...
```

### Clinic Search

```
[Detected: clinics]
Loading clinic database...
Searching for clinics...

Found 10 clinics:

1. DA Clinic @ Simei
   Postal: 520248
   Distance: 0.5 km
   Address: 248 Simei Street 3...
...

📍 Map saved to: /path/to/map.html
Search center: Postal 520123
```

## Confidence Levels

RAG queries show confidence levels based on relevance:

- **High confidence** - Direct matches found
- **Medium confidence** - ℹ️ Partial matches, review carefully
- **Low confidence** - ⚠️ Limited matches, may not be relevant

## Error Handling

### API Not Configured
```
⚠️  No API key configured!
Set OPENAI_API_KEY or DEEPSEEK_API_KEY environment variable.
```

### API Error
```
❌ API Error: Connection failed
```

### Invalid Command
```
Unknown command: /invalid
Type /help for available commands.
```

## Tips for Best Results

1. **Be specific** - Include details about symptoms, duration, severity
2. **One topic at a time** - Focus queries for better results
3. **Use follow-ups** - Build on previous questions naturally
4. **Check confidence** - Low confidence results may need verification
5. **Language mixing** - Supports English and Chinese queries

## Examples Session

```
╔══════════════════════════════════════╗
║          MedBot CLI                  ║
║     AI Medical Assistant             ║
╚══════════════════════════════════════╝

[API: openai connected]

medbot> I have a headache
[Detected: symptoms]
Searching symptoms knowledge base...

Based on your symptoms...
[Response about headaches...]

medbot> what about fever?
[Detected: symptoms]
[Rewritten query: Headache with fever...]

Fever with headache can indicate...
[Response considers both symptoms...]

medbot> /mode doctors
Switched to 'doctors' mode.

medbot> find a Chinese speaking dentist
[Mode: doctors]
Searching for doctors...

Found 3 matching doctors:
1. Dr. Tan Wei Ming - Dental Surgery
   Languages: English, Mandarin
...

medbot> /quit
Goodbye!
```

## Troubleshooting

### CLI won't start
- Check Python version: `python3 --version` (needs 3.9+)
- Install dependencies: `pip3 install -r requirements.txt`

### No responses
- Verify API key is set: `medbot> /status`
- Check internet connection
- Try different model in `.env` file

### Wrong intent detected
- Use `/mode <feature>` to force specific mode
- Be more specific with keywords
- Check `/help` for keyword examples

### Missing data files
Ensure these files exist:
- `Specialists.xlsx` - for doctor search
- `Clinics.xlsx` - for clinic search
- ChromaDB collections - for RAG features

## Feature Parity

The CLI has **100% feature parity** with web interfaces:
- ✅ All 5 features (symptoms, medication, records, doctors, clinics)
- ✅ Conversation history and context
- ✅ Query rewriting for follow-ups
- ✅ Confidence scoring
- ✅ Bilingual support (English/Chinese)
- ✅ Error handling
- ✅ Map generation for clinic search

The only differences are visual presentation (CLI text vs. web UI).
