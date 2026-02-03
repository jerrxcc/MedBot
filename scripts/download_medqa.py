"""
Download and process MedQA dataset.

MedQA: A Dataset for Solving Medical Problems from USMLE Exams
Source: HuggingFace datasets (bigbio/med_qa)
Contains: ~61,097 medical exam questions
  - English (USMLE): 12,723 questions
  - Simplified Chinese: 34,251 questions
  - Traditional Chinese: 14,123 questions

Usage:
    python scripts/download_medqa.py

Output:
    data/raw/medqa/           - Raw JSON files
    data/processed/medqa.jsonl - Processed JSONL file
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP

# =============================================================================
# Configuration
# =============================================================================

RAW_DIR = RAW_DATA_DIR / "medqa"
OUTPUT_FILE = PROCESSED_DATA_DIR / "medqa.jsonl"

# MedQA dataset configurations - using alternative HuggingFace sources
# Primary source: GBaker/MedQA-USMLE-4-options (English USMLE)
# Alternative: openlifescienceai/medqa (if available)
MEDQA_CONFIGS = {
    "usmle_4opt": {
        "name": "USMLE 4-Options",
        "dataset": "GBaker/MedQA-USMLE-4-options",
        "filename": "medqa_usmle.json",
        "language": "en",
        "config": None
    },
    "medqa_main": {
        "name": "MedQA Main",
        "dataset": "openlifescienceai/medqa",
        "filename": "medqa_main.json",
        "language": "en",
        "config": None
    }
}


def download_medqa():
    """Download MedQA dataset from HuggingFace."""
    print("=" * 60)
    print("Downloading MedQA Dataset (USMLE Medical Exams)")
    print("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_data = {}
    total_records = 0

    try:
        from datasets import load_dataset
        print("[INFO] Using HuggingFace datasets library...")

        for config_name, config_info in MEDQA_CONFIGS.items():
            raw_file = RAW_DIR / config_info["filename"]

            if raw_file.exists():
                print(f"[INFO] {config_info['name']} already exists: {raw_file}")
                with open(raw_file, 'r', encoding='utf-8') as f:
                    subset_data = json.load(f)
                all_data.update(subset_data)
                total_records += len(subset_data)
                continue

            print(f"\n[INFO] Downloading {config_info['name']} from {config_info['dataset']}...")

            try:
                # Load dataset with optional config
                if config_info.get("config"):
                    dataset = load_dataset(config_info["dataset"], config_info["config"])
                else:
                    dataset = load_dataset(config_info["dataset"])

                subset_data = {}
                record_count = 0

                for split_name in dataset.keys():
                    split_data = dataset[split_name]
                    print(f"  -> {split_name}: {len(split_data)} records")

                    for i, item in enumerate(split_data):
                        record_id = f"{config_name}_{split_name}_{i}"

                        # Extract question - different datasets use different field names
                        question = item.get("question", "") or item.get("sent1", "")

                        # Handle different option formats
                        # GBaker/MedQA uses: options dict {A: ..., B: ..., C: ..., D: ...}
                        # Others may use list
                        options = item.get("options", {})
                        if isinstance(options, dict):
                            options_list = [f"{k}: {v}" for k, v in sorted(options.items())]
                        elif isinstance(options, list):
                            options_list = options
                        else:
                            # Try individual option fields
                            options_list = []
                            for letter in ['A', 'B', 'C', 'D', 'E']:
                                opt_key = f"ending{ord(letter) - ord('A')}" if f"ending0" in item else letter
                                if opt_key in item:
                                    options_list.append(f"{letter}: {item[opt_key]}")

                        # Get answer - may be letter, index, or text
                        answer = item.get("answer", "") or item.get("answer_idx", "") or item.get("label", "")

                        # Get explanation if available
                        explanation = item.get("exp", "") or item.get("explanation", "")

                        subset_data[record_id] = {
                            "question": question,
                            "options": options_list,
                            "answer": str(answer),
                            "explanation": explanation,
                            "language": config_info["language"],
                            "split": split_name
                        }
                        record_count += 1

                with open(raw_file, 'w', encoding='utf-8') as f:
                    json.dump(subset_data, f, ensure_ascii=False)

                print(f"[SUCCESS] Saved {record_count} records to: {raw_file}")
                all_data.update(subset_data)
                total_records += record_count

            except Exception as e:
                print(f"[WARNING] Failed to download {config_info['name']}: {e}")
                continue

        print(f"\n[SUCCESS] Total MedQA records: {total_records}")
        return total_records > 0

    except ImportError:
        print("[WARNING] HuggingFace datasets library not installed")
        print("[INFO] Install with: pip install datasets")
        return False

    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks at sentence boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            for i in range(min(150, end - start)):
                if text[end - i - 1] in '.!?':
                    end = end - i
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def process_medqa():
    """Process downloaded MedQA data into JSONL format."""
    print("\n" + "=" * 60)
    print("Processing MedQA Data")
    print("=" * 60)

    # Load all raw files
    raw_data = {}
    for config_info in MEDQA_CONFIGS.values():
        raw_file = RAW_DIR / config_info["filename"]
        if raw_file.exists():
            print(f"[INFO] Loading: {raw_file.name}")
            with open(raw_file, 'r', encoding='utf-8') as f:
                subset_data = json.load(f)
                raw_data.update(subset_data)
                print(f"  -> {len(subset_data)} records")

    if not raw_data:
        print("[ERROR] No raw data found. Please download first.")
        return False

    print(f"\n[INFO] Total loaded: {len(raw_data)} QA entries")

    all_data = []
    doc_id = 0

    for record_id, entry in raw_data.items():
        question = entry.get("question", "")
        options = entry.get("options", [])
        answer = entry.get("answer", "")
        explanation = entry.get("explanation", "")
        language = entry.get("language", "en")

        if not question:
            continue

        # Build comprehensive content
        content_parts = [f"Question: {question}"]

        if options:
            content_parts.append("Options:")
            for j, opt in enumerate(options):
                # Format option - check if already has letter prefix
                if isinstance(opt, str):
                    if opt.startswith(('A:', 'B:', 'C:', 'D:', 'E:')):
                        content_parts.append(f"  {opt}")
                    else:
                        letter = chr(65 + j)  # A, B, C, D, E
                        content_parts.append(f"  {letter}. {opt}")

        if answer:
            content_parts.append(f"\nCorrect Answer: {answer}")

        if explanation:
            content_parts.append(f"\nExplanation: {explanation}")

        content = "\n".join(content_parts)

        # Chunk if necessary
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            doc_id += 1

            record = {
                "id": f"medqa_{doc_id:06d}",
                "content": chunk,
                "metadata": {
                    "source": "MedQA",
                    "category": "Medical Exam",
                    "language": language,
                    "question": question[:200],
                    "chunk_index": i if len(chunks) > 1 else None
                }
            }
            all_data.append(record)

    # Save processed data
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for record in all_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"\n[SUCCESS] Processed {len(all_data)} records from {len(raw_data)} QA pairs")
    print(f"[SUCCESS] Saved to: {OUTPUT_FILE}")

    if all_data:
        print("\n[SAMPLE] First record:")
        print(json.dumps(all_data[0], indent=2, ensure_ascii=False)[:800] + "...")

    return True


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("MedQA Data Pipeline")
    print("=" * 60)

    if not download_medqa():
        print("\n[INFO] Please install dependencies and run again:")
        print("  pip install datasets")
        return

    process_medqa()

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
