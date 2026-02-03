"""
Download and process PubMedQA dataset.

PubMedQA: A Dataset for Biomedical Research Question Answering
Source: HuggingFace datasets (qiaojin/PubMedQA)
Contains: ~5,000 expert-annotated QA pairs from PubMed abstracts

Usage:
    python scripts/download_pubmedqa.py

Output:
    data/raw/pubmedqa/           - Raw JSON file
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
    """Download PubMedQA dataset from HuggingFace."""
    print("=" * 60)
    print("Downloading PubMedQA Dataset")
    print("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_file = RAW_DIR / "pubmedqa_raw.json"

    if raw_file.exists():
        print(f"[INFO] Raw file already exists: {raw_file}")
        return True

    # Try HuggingFace datasets library first
    try:
        from datasets import load_dataset
        print("[INFO] Using HuggingFace datasets library...")

        # Load the pqa_labeled split (expert-annotated)
        dataset = load_dataset("qiaojin/PubMedQA", "pqa_labeled", split="train")
        print(f"[INFO] Loaded {len(dataset)} records from HuggingFace")

        # Convert to dict format
        data = {}
        for i, item in enumerate(dataset):
            pmid = item.get("pubid", str(i))
            data[pmid] = {
                "QUESTION": item.get("question", ""),
                "CONTEXTS": item.get("context", {}).get("contexts", []),
                "LONG_ANSWER": item.get("long_answer", ""),
                "final_decision": item.get("final_decision", "")
            }

        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[SUCCESS] Downloaded to: {raw_file}")
        return True

    except ImportError:
        print("[WARNING] HuggingFace datasets library not installed")
        print("[INFO] Install with: pip install datasets")

    except Exception as e:
        print(f"[ERROR] HuggingFace download failed: {e}")

    # Fallback: try direct URL download
    import urllib.request
    urls = [
        "https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqaa.json",
        "https://raw.githubusercontent.com/pubmedqa/pubmedqa/main/data/ori_pqaa.json",
    ]

    for url in urls:
        try:
            print(f"[INFO] Trying: {url}")
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read().decode('utf-8')
                with open(raw_file, 'w', encoding='utf-8') as f:
                    f.write(data)
            print(f"[SUCCESS] Downloaded to: {raw_file}")
            return True
        except Exception as e:
            print(f"[WARNING] URL failed: {e}")
            continue

    print("\n[ERROR] All download methods failed")
    print("\n[ALTERNATIVE] Install HuggingFace datasets:")
    print("  pip install datasets")
    print("  Then run this script again")
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

    raw_file = RAW_DIR / "pubmedqa_raw.json"

    if not raw_file.exists():
        print("[ERROR] Raw data not found. Please download first.")
        return False

    print(f"[INFO] Loading data from: {raw_file}")

    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f"[INFO] Loaded {len(raw_data)} QA entries")

    all_data = []
    doc_id = 0

    for pmid, entry in raw_data.items():
        question = entry.get("QUESTION", "")
        contexts = entry.get("CONTEXTS", [])
        long_answer = entry.get("LONG_ANSWER", "")
        final_decision = entry.get("final_decision", "")

        if not question or not long_answer:
            continue

        # Combine context paragraphs
        context_text = " ".join(contexts) if contexts else ""

        # Build comprehensive content
        content_parts = [f"Question: {question}"]

        if context_text:
            content_parts.append(f"Context: {context_text[:800]}")

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
