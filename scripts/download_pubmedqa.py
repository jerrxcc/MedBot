"""
Download and process PubMedQA dataset.

PubMedQA: A Dataset for Biomedical Research Question Answering
Source: HuggingFace datasets (qiaojin/PubMedQA)
Contains: ~273,518 QA pairs from PubMed abstracts
  - pqa_labeled: 1,000 expert-annotated
  - pqa_unlabeled: 61,249 unlabeled
  - pqa_artificial: 211,269 automatically generated

Usage:
    python scripts/download_pubmedqa.py

Output:
    data/raw/pubmedqa/           - Raw JSON files
    data/processed/pubmedqa.jsonl - Processed JSONL file
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP

# =============================================================================
# Configuration
# =============================================================================

RAW_DIR = RAW_DATA_DIR / "pubmedqa"
OUTPUT_FILE = PROCESSED_DATA_DIR / "pubmedqa.jsonl"


def download_pubmedqa():
    """Download all PubMedQA subsets from HuggingFace (~273K records)."""
    print("=" * 60)
    print("Downloading PubMedQA Dataset (All Subsets)")
    print("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Define all subsets to download
    subsets = {
        "pqa_labeled": "pubmedqa_labeled.json",      # 1K expert-annotated
        "pqa_unlabeled": "pubmedqa_unlabeled.json",  # 61K unlabeled
        "pqa_artificial": "pubmedqa_artificial.json" # 211K auto-generated
    }

    all_data = {}
    total_records = 0

    try:
        from datasets import load_dataset
        print("[INFO] Using HuggingFace datasets library...")

        for subset_name, filename in subsets.items():
            raw_file = RAW_DIR / filename

            if raw_file.exists():
                print(f"[INFO] {subset_name} already exists: {raw_file}")
                # Load existing data
                with open(raw_file, 'r', encoding='utf-8') as f:
                    subset_data = json.load(f)
                all_data.update(subset_data)
                total_records += len(subset_data)
                continue

            print(f"\n[INFO] Downloading {subset_name}...")

            try:
                dataset = load_dataset("qiaojin/PubMedQA", subset_name, split="train")
                print(f"[INFO] Loaded {len(dataset)} records from {subset_name}")

                # Convert to dict format
                subset_data = {}
                for i, item in enumerate(dataset):
                    pmid = item.get("pubid", f"{subset_name}_{i}")

                    # Handle context which may be dict or list
                    contexts = item.get("context", {})
                    if isinstance(contexts, dict):
                        context_list = contexts.get("contexts", [])
                    elif isinstance(contexts, list):
                        context_list = contexts
                    else:
                        context_list = []

                    subset_data[pmid] = {
                        "QUESTION": item.get("question", ""),
                        "CONTEXTS": context_list,
                        "LONG_ANSWER": item.get("long_answer", ""),
                        "final_decision": item.get("final_decision", ""),
                        "subset": subset_name
                    }

                with open(raw_file, 'w', encoding='utf-8') as f:
                    json.dump(subset_data, f, ensure_ascii=False)

                print(f"[SUCCESS] Saved {len(subset_data)} records to: {raw_file}")
                all_data.update(subset_data)
                total_records += len(subset_data)

            except Exception as e:
                print(f"[WARNING] Failed to download {subset_name}: {e}")
                continue

        print(f"\n[SUCCESS] Total PubMedQA records: {total_records}")
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


def process_pubmedqa():
    """Process downloaded PubMedQA data into JSONL format."""
    print("\n" + "=" * 60)
    print("Processing PubMedQA Data")
    print("=" * 60)

    # Load all subset files
    raw_files = [
        RAW_DIR / "pubmedqa_labeled.json",
        RAW_DIR / "pubmedqa_unlabeled.json",
        RAW_DIR / "pubmedqa_artificial.json",
        RAW_DIR / "pubmedqa_raw.json"  # Legacy file for backward compatibility
    ]

    raw_data = {}
    for raw_file in raw_files:
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

    for pmid, entry in raw_data.items():
        question = entry.get("QUESTION", "")
        contexts = entry.get("CONTEXTS", [])
        long_answer = entry.get("LONG_ANSWER", "")
        final_decision = entry.get("final_decision", "")
        subset = entry.get("subset", "unknown")

        if not question or not long_answer:
            continue

        # Combine context paragraphs
        context_text = " ".join(contexts) if contexts else ""

        # Build comprehensive content
        content_parts = [f"Question: {question}"]

        if context_text:
            # Limit context to preserve answer visibility
            content_parts.append(f"Context: {context_text[:600]}")

        content_parts.append(f"Answer: {long_answer}")

        if final_decision:
            content_parts.append(f"Conclusion: {final_decision}")

        content = "\n\n".join(content_parts)

        # Chunk if necessary
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            doc_id += 1

            record = {
                "id": f"pubmedqa_{doc_id:06d}",
                "content": chunk,
                "metadata": {
                    "source": "PubMedQA",
                    "category": "Medical QA",
                    "pmid": pmid,
                    "question": question[:200],
                    "decision": final_decision,
                    "subset": subset,
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
        print(json.dumps(all_data[0], indent=2, ensure_ascii=False)[:600] + "...")

    return True


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("PubMedQA Data Pipeline")
    print("=" * 60)

    if not download_pubmedqa():
        print("\n[INFO] Please download manually and run again.")
        return

    process_pubmedqa()

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
