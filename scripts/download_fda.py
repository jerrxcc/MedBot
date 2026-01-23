"""
Download and process FDA Drug Labels data.

Source: OpenFDA API (https://open.fda.gov/apis/drug/label/)
Contains: Drug labels with usage, warnings, side effects, etc.

Usage:
    python scripts/download_fda.py

Output:
    data/raw/fda_drugs/           - Raw JSON responses
    data/processed/medications.jsonl - Processed JSONL file
"""

import os
import sys
import json
import time
from pathlib import Path
import urllib.request
import urllib.parse

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

FDA_API_BASE = "https://api.fda.gov/drug/label.json"
RAW_DIR = RAW_DATA_DIR / "fda_drugs"
OUTPUT_FILE = PROCESSED_DATA_DIR / "medications.jsonl"

DRUG_CATEGORIES = [
    "pain", "fever", "antibiotic", "diabetes", "blood pressure",
    "cholesterol", "depression", "anxiety", "allergy", "asthma",
    "heart", "stomach", "sleep", "vitamin", "infection"
]

RESULTS_PER_CATEGORY = 50
API_DELAY = 0.5


def fetch_fda_data(search_term, limit=50):
    """Fetch drug data from OpenFDA API."""
    params = {
        "search": f"openfda.brand_name:{search_term} OR purpose:{search_term}",
        "limit": limit
    }

    url = f"{FDA_API_BASE}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data.get("results", [])
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[INFO] No results for: {search_term}")
            return []
        print(f"[WARNING] HTTP error for {search_term}: {e}")
        return []
    except Exception as e:
        print(f"[WARNING] Error fetching {search_term}: {e}")
        return []


def download_fda_data():
    """Download FDA drug data for common categories."""
    print("=" * 60)
    print("Downloading FDA Drug Labels")
    print("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_drugs = []
    seen_ids = set()

    for category in DRUG_CATEGORIES:
        print(f"[INFO] Fetching: {category}...")

        results = fetch_fda_data(category, RESULTS_PER_CATEGORY)

        for drug in results:
            drug_id = drug.get("id", "")
            if drug_id and drug_id not in seen_ids:
                seen_ids.add(drug_id)
                all_drugs.append(drug)

        print(f"       Found {len(results)} results, {len(all_drugs)} total unique")
        time.sleep(API_DELAY)

    raw_file = RAW_DIR / "fda_drugs_raw.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(all_drugs, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Downloaded {len(all_drugs)} unique drug records")
    print(f"[SUCCESS] Saved raw data to: {raw_file}")

    return all_drugs


def extract_text_field(drug_record, field_name):
    """Safely extract text from a drug record field."""
    value = drug_record.get(field_name, [])

    if isinstance(value, list):
        return " ".join(str(v) for v in value if v)
    elif isinstance(value, str):
        return value
    else:
        return ""


def process_drug_record(drug_record, doc_id):
    """Process a single drug record into standard format."""
    openfda = drug_record.get("openfda", {})
    brand_names = openfda.get("brand_name", [])
    generic_names = openfda.get("generic_name", [])

    drug_name = (brand_names[0] if brand_names
                 else generic_names[0] if generic_names
                 else None)

    if not drug_name:
        return None

    purpose = extract_text_field(drug_record, "purpose")
    indications = extract_text_field(drug_record, "indications_and_usage")
    dosage = extract_text_field(drug_record, "dosage_and_administration")
    warnings = extract_text_field(drug_record, "warnings")
    side_effects = extract_text_field(drug_record, "adverse_reactions")

    content_parts = [f"Drug: {drug_name}"]

    if purpose:
        content_parts.append(f"Purpose: {purpose[:500]}")
    if indications:
        content_parts.append(f"Uses: {indications[:500]}")
    if dosage:
        content_parts.append(f"Dosage: {dosage[:300]}")
    if warnings:
        content_parts.append(f"Warnings: {warnings[:400]}")
    if side_effects:
        content_parts.append(f"Side Effects: {side_effects[:400]}")

    content = "\n\n".join(content_parts)

    if len(content) < 100:
        return None

    if len(content) > 2000:
        content = content[:2000] + "..."

    pharm_class = openfda.get("pharm_class_epc", [])
    category = pharm_class[0] if pharm_class else "General"

    return {
        "id": f"fda_{doc_id:06d}",
        "content": content,
        "metadata": {
            "source": "FDA",
            "drug_name": drug_name,
            "category": category[:100] if category else "General",
            "usage": (indications[:200] if indications else "")[:200],
            "warnings": (warnings[:200] if warnings else "")[:200]
        }
    }


def process_fda_data(raw_data=None):
    """Process FDA data into JSONL format."""
    print("\n" + "=" * 60)
    print("Processing FDA Drug Data")
    print("=" * 60)

    if raw_data is None:
        raw_file = RAW_DIR / "fda_drugs_raw.json"
        if not raw_file.exists():
            print("[ERROR] Raw data not found. Please run download first.")
            return False

        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

    print(f"[INFO] Processing {len(raw_data)} drug records...")

    processed = []
    doc_id = 0

    for drug in raw_data:
        doc_id += 1
        record = process_drug_record(drug, doc_id)
        if record:
            processed.append(record)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for record in processed:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"\n[SUCCESS] Processed {len(processed)} valid drug records")
    print(f"[SUCCESS] Saved to: {OUTPUT_FILE}")

    if processed:
        print("\n[SAMPLE] First record:")
        print(json.dumps(processed[0], indent=2, ensure_ascii=False)[:600] + "...")

    return True


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("FDA Drug Data Pipeline")
    print("=" * 60)

    raw_file = RAW_DIR / "fda_drugs_raw.json"
    if raw_file.exists():
        print("[INFO] Raw data exists, skipping download.")
        raw_data = None
    else:
        raw_data = download_fda_data()

    process_fda_data(raw_data)

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
