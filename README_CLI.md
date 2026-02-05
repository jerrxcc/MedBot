# MedBot CLI - Developer Testing Tool

## Purpose

This CLI is a **developer tool** for quick testing and debugging of MedBot functionality. End users will use the web UI interfaces (Gradio/Chainlit).

## Quick Start

```bash
# Install dependencies
pip3 install prompt-toolkit rapidfuzz openpyxl pandas

# Run CLI
python3 cli.py
```

## Testing Commands

### Quick Feature Tests

```bash
# Test symptoms
echo "I have a headache" | python3 cli.py

# Test medication
echo "side effects of aspirin" | python3 cli.py

# Test doctor search
echo "find a dentist" | python3 cli.py

# Test clinic search
echo "clinic near 520123" | python3 cli.py
```

### Test Scripts

Create test files for automated testing:

```bash
cat > test_all.txt << 'EOF'
I feel dizzy
side effects of ibuprofen
what is diabetes
find a cardiologist
clinic near Tampines
/status
/quit
EOF

python3 cli.py < test_all.txt
```

## Developer Benefits

1. **Fast Testing** - No browser/server startup needed
2. **Scriptable** - Easy to automate test scenarios
3. **Debug Friendly** - Direct terminal output for errors
4. **Feature Parity** - Tests all UI features
5. **Portable** - Works anywhere Python runs

## Architecture

```
cli.py (entry point)
└── src/cli/
    ├── repl.py          # Main REPL loop
    ├── intent.py        # Intent detection (keyword-based)
    ├── handlers.py      # Feature routing
    ├── commands.py      # Slash commands
    ├── history.py       # Conversation state
    └── completer.py     # Auto-completion
```

## Key Features

- ✅ Auto intent detection (symptoms/medication/records/doctors/clinics)
- ✅ Slash commands for control (/help, /mode, /status, etc.)
- ✅ Conversation history (10 turns)
- ✅ Context-aware follow-ups
- ✅ Bilingual support (EN/CN)
- ✅ Error handling and validation

## Testing Checklist

- [x] Symptom queries → RAG retrieval works
- [x] Medication queries → FDA data retrieved
- [x] Records queries → Medical info retrieved
- [x] Doctor search → Agent returns results
- [x] Clinic search → Location search + distance calculation
- [x] Follow-up questions → Context preserved
- [x] Mode switching → Forces specific intent
- [x] Error handling → API errors caught
- [x] Chinese input → Detected and processed
- [x] Invalid commands → Helpful error messages

## Fixed Issues

| Issue | Fix |
|-------|-----|
| Temperature param error | Removed unsupported parameter |
| Python 3.9 type unions | Changed to Optional[Dict] |
| Intent detection priority | Added priority rules |

## Usage Examples

### Test New Prompts

```bash
python3 cli.py
medbot> [paste new prompt here]
# Observe: intent detection, RAG results, response quality
```

### Debug RAG Retrieval

```bash
# Check confidence levels
medbot> my symptom query
[Detected: symptoms]
Searching symptoms knowledge base...
⚠️  Low confidence match  # ← indicates retrieval issues
```

### Test Conversation Flow

```bash
medbot> I have a headache
[Response...]
medbot> what about fever?
[Rewritten query: ...]  # ← verify context understanding
```

### Test Edge Cases

```bash
# Special characters
medbot> headache & fever?? (urgent!)

# Long input
medbot> [paste very long description]

# Mixed language
medbot> I feel 头痛

# Empty input
medbot>
# Should skip silently
```

## Debugging Tips

1. **Check API status first:** `medbot> /status`
2. **View history:** `medbot> /history`
3. **Force specific mode:** `medbot> /mode symptoms`
4. **Clear state:** `medbot> /clear`
5. **Check files:** Specialists.xlsx and Clinics.xlsx must exist

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Startup | ~2s | One-time model loading |
| Intent detection | <100ms | Keyword-based |
| RAG query | 3-5s | Retrieval + LLM |
| Search | 2-4s | LLM intent + search |

## File Locations

```
MED_BOT/
├── cli.py                    # Entry point
├── CLI_GUIDE.md              # User documentation
├── CLI_TEST_REPORT.md        # Test results
└── src/cli/                  # CLI implementation
    ├── __init__.py
    ├── repl.py               # Main loop
    ├── intent.py             # Detection logic
    ├── handlers.py           # Feature handlers
    ├── commands.py           # Slash commands
    ├── history.py            # Conversation state
    └── completer.py          # Auto-completion
```

## Integration with Existing Code

The CLI reuses all existing modules:
- `src/retriever.py` - RAG retrieval
- `src/llm.py` - LLM calls
- `src/prompts.py` - System prompts
- `src/search_agent.py` - Doctor search
- `src/clinic_search.py` - Clinic search

**No changes to core functionality** - CLI is a pure interface layer.

## When to Use

**Use CLI for:**
- ✅ Quick functionality tests
- ✅ Debugging RAG retrieval
- ✅ Testing new prompts
- ✅ Verifying intent detection
- ✅ Automated test scripts
- ✅ CI/CD integration

**Use Web UI for:**
- End-user interactions
- Demo presentations
- Visual feedback needs
- File uploads (future)
- Multi-modal content

## Future Enhancements (if needed)

- [ ] Export test results to JSON
- [ ] Batch testing from file
- [ ] Performance profiling mode
- [ ] Mock API responses for unit tests
- [ ] Integration with pytest

## Summary

The CLI provides a **fast, scriptable way** to test all MedBot features without the overhead of launching web servers. Perfect for development and CI/CD pipelines while maintaining 100% feature parity with production UI.
