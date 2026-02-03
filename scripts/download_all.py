"""
Download and process all datasets for MedBot.

This script runs all data download and processing pipelines in sequence.

Usage:
    python scripts/download_all.py

Output:
    data/processed/symptoms.jsonl     - From MedQuAD (~35K)
    data/processed/medications.jsonl  - From FDA (~1.8K)
    data/processed/records.jsonl      - From MTSamples (~6)
    data/processed/pubmedqa.jsonl     - From PubMedQA (~273K)
    data/processed/medqa.jsonl        - From MedQA (~61K)

Total: ~287K medical QA records
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.download_medquad import main as download_medquad
from scripts.download_fda import main as download_fda
from scripts.download_mtsamples import main as download_mtsamples
from scripts.download_pubmedqa import main as download_pubmedqa
from scripts.download_medqa import main as download_medqa


def main():
    """Run all data download pipelines."""
    print("\n" + "=" * 70)
    print("  MedBot Data Download Pipeline - All Datasets (~287K records)")
    print("=" * 70)

    # Track results
    results = {}

    # 1. MedQuAD
    print("\n\n" + "=" * 70)
    print("  [1/5] MedQuAD Dataset (~35K)")
    print("=" * 70)
    try:
        download_medquad()
        results["MedQuAD"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] MedQuAD failed: {e}")
        results["MedQuAD"] = f"FAILED: {e}"

    # 2. FDA
    print("\n\n" + "=" * 70)
    print("  [2/5] FDA Drug Labels (~1.8K)")
    print("=" * 70)
    try:
        download_fda()
        results["FDA"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] FDA failed: {e}")
        results["FDA"] = f"FAILED: {e}"

    # 3. MTSamples
    print("\n\n" + "=" * 70)
    print("  [3/5] MTSamples Medical Records")
    print("=" * 70)
    try:
        download_mtsamples()
        results["MTSamples"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] MTSamples failed: {e}")
        results["MTSamples"] = f"FAILED: {e}"

    # 4. PubMedQA
    print("\n\n" + "=" * 70)
    print("  [4/5] PubMedQA Dataset (~273K)")
    print("=" * 70)
    try:
        download_pubmedqa()
        results["PubMedQA"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] PubMedQA failed: {e}")
        results["PubMedQA"] = f"FAILED: {e}"

    # 5. MedQA
    print("\n\n" + "=" * 70)
    print("  [5/5] MedQA USMLE Dataset (~61K)")
    print("=" * 70)
    try:
        download_medqa()
        results["MedQA"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] MedQA failed: {e}")
        results["MedQA"] = f"FAILED: {e}"

    # Summary
    print("\n\n" + "=" * 70)
    print("  Download Summary")
    print("=" * 70)
    for dataset, status in results.items():
        status_icon = "[OK]" if status == "SUCCESS" else "[X]"
        print(f"  {status_icon} {dataset}: {status}")

    print("\n" + "=" * 70)
    print("  All Downloads Complete!")
    print("=" * 70)
    print("\n  Next step: Run 'python scripts/build_vectorstore.py --clear'")


if __name__ == "__main__":
    main()
