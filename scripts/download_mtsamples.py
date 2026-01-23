"""
Download and process MTSamples medical transcription data.

Source: MTSamples (https://mtsamples.com/)
Note: We use a preprocessed version from Kaggle for easier access.

Dataset: https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions

Usage:
    python scripts/download_mtsamples.py

Output:
    data/raw/mtsamples/           - Raw CSV file
    data/processed/records.jsonl  - Processed JSONL file

IMPORTANT: You need to download the dataset manually from Kaggle:
    1. Go to: https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions
    2. Download 'mtsamples.csv'
    3. Place it in: data/raw/mtsamples/mtsamples.csv
"""

import os
import sys
import json
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP

RAW_DIR = RAW_DATA_DIR / "mtsamples"
RAW_FILE = RAW_DIR / "mtsamples.csv"
OUTPUT_FILE = PROCESSED_DATA_DIR / "records.jsonl"

CREATE_SAMPLE_DATA = True

SAMPLE_RECORDS = [
    {
        "specialty": "General Medicine",
        "document_type": "Consultation Note",
        "transcription": """CHIEF COMPLAINT: Chest pain and shortness of breath.

HISTORY OF PRESENT ILLNESS: The patient is a 58-year-old male who presents to the emergency department with complaints of chest pain and shortness of breath that started approximately 2 hours ago. The pain is described as pressure-like, located in the substernal area, radiating to the left arm. The patient rates the pain as 7/10 in intensity.

PAST MEDICAL HISTORY: Hypertension, Type 2 Diabetes Mellitus, Hyperlipidemia.

MEDICATIONS: Lisinopril 10mg daily, Metformin 500mg twice daily, Atorvastatin 20mg daily.

PHYSICAL EXAMINATION:
- Vital Signs: BP 158/92, HR 98, RR 22, Temp 98.6F, SpO2 94% on room air
- General: Alert, anxious, in moderate distress
- Cardiovascular: Regular rhythm, no murmurs, S1 and S2 normal
- Respiratory: Bilateral breath sounds clear, no wheezes or crackles

ASSESSMENT AND PLAN: 58-year-old male with cardiovascular risk factors presenting with acute chest pain concerning for acute coronary syndrome. Will obtain EKG, cardiac enzymes, chest X-ray. Start aspirin 325mg, nitroglycerin as needed. Cardiology consult requested."""
    },
    {
        "specialty": "Neurology",
        "document_type": "Consultation Note",
        "transcription": """CHIEF COMPLAINT: Severe headache and dizziness.

HISTORY OF PRESENT ILLNESS: This is a 45-year-old female presenting with severe headache that began suddenly this morning. She describes it as the worst headache of her life, rated 9/10 in intensity. The headache is associated with nausea, vomiting, and photophobia.

PAST MEDICAL HISTORY: Migraine headaches (well-controlled), no prior history of similar severe headache.

MEDICATIONS: Sumatriptan 50mg PRN for migraines.

PHYSICAL EXAMINATION:
- Vital Signs: BP 142/88, HR 88, RR 18, Temp 99.2F
- Neurological: Alert and oriented x3, cranial nerves II-XII intact, no focal motor or sensory deficits
- Neck: Mild nuchal rigidity noted

ASSESSMENT: Acute severe headache with concerning features including sudden onset, neck stiffness, and fever. Differential includes subarachnoid hemorrhage, meningitis, or complicated migraine.

PLAN: Urgent CT head without contrast, if negative proceed with lumbar puncture. Blood cultures, CBC, CMP. Empiric antibiotics if meningitis suspected."""
    },
    {
        "specialty": "Emergency Room Reports",
        "document_type": "ER Report",
        "transcription": """CHIEF COMPLAINT: Motor vehicle accident.

HISTORY OF PRESENT ILLNESS: The patient is a 28-year-old female who was the restrained driver in a motor vehicle collision. She was traveling approximately 35 mph when her vehicle was struck on the driver's side by another vehicle. Airbags deployed. She was able to self-extricate.

PHYSICAL EXAMINATION:
- Primary Survey: Airway intact, breathing unlabored, circulation intact
- Vital Signs: BP 132/78, HR 92, RR 18, SpO2 99%
- HEENT: No facial trauma, pupils equal and reactive, C-collar in place
- Chest: Tenderness to palpation over left lateral ribs 5-7
- Extremities: Left forearm with swelling and tenderness, good distal pulses
- Neurological: GCS 15, moves all extremities

IMAGING:
- CT Head: Negative for acute intracranial pathology
- CT C-spine: No fracture or malalignment
- CT Chest: Left rib fractures 5, 6, and 7 without pneumothorax
- X-ray left forearm: Distal radius fracture

ASSESSMENT AND PLAN: MVA with left rib fractures and left distal radius fracture. Admit for pain control and monitoring. Orthopedic consult for forearm fracture management."""
    }
]


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            for i in range(min(150, end - start)):
                if text[end - i - 1] in '\n.!?':
                    end = end - i
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def process_csv_file():
    """Process MTSamples CSV file into JSONL format."""
    print("=" * 60)
    print("Processing MTSamples CSV Data")
    print("=" * 60)

    if not RAW_FILE.exists():
        print(f"[ERROR] CSV file not found: {RAW_FILE}")
        print("\n[INSTRUCTIONS] Please download manually:")
        print("1. Go to: https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions")
        print("2. Download 'mtsamples.csv'")
        print(f"3. Place it in: {RAW_FILE}")
        return None

    print(f"[INFO] Reading: {RAW_FILE}")

    processed = []
    doc_id = 0

    with open(RAW_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)

        for row in reader:
            specialty = row.get('medical_specialty', '').strip()
            transcription = row.get('transcription', '').strip()
            description = row.get('description', '').strip()

            if not transcription or len(transcription) < 100:
                continue

            chunks = chunk_text(transcription)

            for i, chunk in enumerate(chunks):
                doc_id += 1

                record = {
                    "id": f"mtsamples_{doc_id:06d}",
                    "content": chunk,
                    "metadata": {
                        "source": "MTSamples",
                        "specialty": specialty or "General",
                        "document_type": description[:100] if description else "Medical Record",
                        "sample_type": "transcription",
                        "chunk_index": i if len(chunks) > 1 else None
                    }
                }
                processed.append(record)

    return processed


def create_sample_data():
    """Create sample data when Kaggle file is not available."""
    print("=" * 60)
    print("Creating Sample Medical Records Data")
    print("=" * 60)
    print("[INFO] Using built-in sample records (for demo purposes)")

    processed = []
    doc_id = 0

    for sample in SAMPLE_RECORDS:
        chunks = chunk_text(sample["transcription"])

        for i, chunk in enumerate(chunks):
            doc_id += 1

            record = {
                "id": f"mtsamples_{doc_id:06d}",
                "content": chunk,
                "metadata": {
                    "source": "MTSamples",
                    "specialty": sample["specialty"],
                    "document_type": sample["document_type"],
                    "sample_type": "template",
                    "chunk_index": i if len(chunks) > 1 else None
                }
            }
            processed.append(record)

    return processed


def save_processed_data(data):
    """Save processed data to JSONL file."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"\n[SUCCESS] Saved {len(data)} records to: {OUTPUT_FILE}")

    if data:
        print("\n[SAMPLE] First record:")
        print(json.dumps(data[0], indent=2, ensure_ascii=False)[:600] + "...")


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("MTSamples Data Pipeline")
    print("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    data = process_csv_file()

    if data is None and CREATE_SAMPLE_DATA:
        print("\n[INFO] Falling back to sample data...")
        data = create_sample_data()

    if data:
        save_processed_data(data)

    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
