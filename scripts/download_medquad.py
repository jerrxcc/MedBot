"""
Download and process MedQuAD dataset.

MedQuAD: Medical Question Answering Dataset
Source: https://github.com/abachaa/MedQuAD
Contains: 47,457 QA pairs from trusted medical sources (NIH)

Usage:
    python scripts/download_medquad.py

Output:
    data/raw/medquad/           - Raw XML files
    data/processed/symptoms.jsonl - Processed JSONL file
"""

import os
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import urllib.request
import zipfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP

# =============================================================================
# Configuration
# =============================================================================

MEDQUAD_REPO = "https://github.com/abachaa/MedQuAD/archive/refs/heads/master.zip"
RAW_DIR = RAW_DATA_DIR / "medquad"
OUTPUT_FILE = PROCESSED_DATA_DIR / "symptoms.jsonl"

# Relevant subdirectories in MedQuAD (focus on symptoms and diseases)
RELEVANT_DIRS = [
    "1_CancerGov_QA",
    "2_GARD_QA",
    "3_GHR_QA",
    "4_MPlus_Health_Topics_QA",
    "5_NIDDK_QA",
    "6_NINDS_QA",
    "8_NHLBI_QA_XML",
    "9_CDC_QA"
]


def download_medquad():
    """Download MedQuAD dataset from GitHub."""
    print("=" * 60)
    print("Downloading MedQuAD Dataset")
    print("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / "medquad.zip"

    if zip_path.exists():
        print(f"[INFO] Zip file already exists: {zip_path}")
    else:
        print(f"[INFO] Downloading from: {MEDQUAD_REPO}")
        print("[INFO] This may take a few minutes...")

        try:
            urllib.request.urlretrieve(MEDQUAD_REPO, zip_path)
            print(f"[SUCCESS] Downloaded to: {zip_path}")
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            print("\n[ALTERNATIVE] Manual download instructions:")
            print("1. Go to: https://github.com/abachaa/MedQuAD")
            print("2. Click 'Code' -> 'Download ZIP'")
            print(f"3. Save as: {zip_path}")
            return False

    print(f"[INFO] Extracting...")
    extract_dir = RAW_DIR / "extracted"

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"[SUCCESS] Extracted to: {extract_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return False


def parse_xml_file(filepath):
    """Parse a MedQuAD XML file and extract QA pairs."""
    qa_pairs = []

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        focus = root.find('.//Focus')
        focus_text = focus.text if focus is not None else ""

        url = root.find('.//Url')
        url_text = url.text if url is not None else ""

        for qa_section in root.findall('.//QAPair'):
            question = qa_section.find('Question')
            answer = qa_section.find('Answer')

            if question is not None and answer is not None:
                q_text = question.text or ""
                a_text = answer.text or ""

                if q_text.strip() and a_text.strip():
                    qa_pairs.append({
                        'question': q_text.strip(),
                        'answer': a_text.strip(),
                        'focus': focus_text.strip(),
                        'url': url_text.strip()
                    })

    except ET.ParseError as e:
        print(f"[WARNING] XML parse error in {filepath}: {e}")
    except Exception as e:
        print(f"[WARNING] Error processing {filepath}: {e}")

    return qa_pairs


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            for i in range(min(100, end - start)):
                if text[end - i - 1] in '.!?':
                    end = end - i
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def process_medquad():
    """Process downloaded MedQuAD data into JSONL format."""
    print("\n" + "=" * 60)
    print("Processing MedQuAD Data")
    print("=" * 60)

    extract_dir = RAW_DIR / "extracted"
    medquad_dir = None

    for item in extract_dir.iterdir():
        if item.is_dir() and "MedQuAD" in item.name:
            medquad_dir = item
            break

    if not medquad_dir:
        print("[ERROR] MedQuAD directory not found. Please download first.")
        return False

    print(f"[INFO] Processing from: {medquad_dir}")

    all_data = []
    doc_id = 0

    for subdir_name in RELEVANT_DIRS:
        subdir = medquad_dir / subdir_name

        if not subdir.exists():
            print(f"[WARNING] Directory not found: {subdir_name}")
            continue

        xml_files = list(subdir.glob("*.xml"))
        print(f"[INFO] Processing {subdir_name}: {len(xml_files)} files")

        for xml_file in xml_files:
            qa_pairs = parse_xml_file(xml_file)

            for qa in qa_pairs:
                content = f"Question: {qa['question']}\n\nAnswer: {qa['answer']}"
                chunks = chunk_text(content)

                for i, chunk in enumerate(chunks):
                    doc_id += 1

                    record = {
                        "id": f"medquad_{doc_id:06d}",
                        "content": chunk,
                        "metadata": {
                            "source": "MedQuAD",
                            "category": "Symptoms",
                            "condition": qa['focus'],
                            "url": qa['url'],
                            "chunk_index": i if len(chunks) > 1 else None
                        }
                    }
                    all_data.append(record)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for record in all_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"\n[SUCCESS] Processed {len(all_data)} records")
    print(f"[SUCCESS] Saved to: {OUTPUT_FILE}")

    if all_data:
        print("\n[SAMPLE] First record:")
        print(json.dumps(all_data[0], indent=2, ensure_ascii=False)[:500] + "...")

    return True


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("MedQuAD Data Pipeline")
    print("=" * 60)

    if not (RAW_DIR / "extracted").exists():
        success = download_medquad()
        if not success:
            print("\n[INFO] Please download manually and run again.")
            return
    else:
        print("[INFO] Data already downloaded, skipping download step.")

    process_medquad()

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
