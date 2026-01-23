"""
Download and process all datasets for MedBot.

This script runs all data download and processing pipelines in sequence.

Usage:
    python scripts/download_all.py

Output:
    data/processed/symptoms.jsonl     - From MedQuAD
    data/processed/medications.jsonl  - From FDA
    data/processed/records.jsonl      - From MTSamples
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.download_medquad import main as download_medquad
from scripts.download_fda import main as download_fda
from scripts.download_mtsamples import main as download_mtsamples


def main():
    """Run all data download pipelines."""
    print("\n" + "=" * 70)
    print("  MedBot Data Download Pipeline - All Datasets")
    print("=" * 70)

    # Track results
    results = {}

    # 1. MedQuAD
    print("\n\n" + "=" * 70)
    print("  [1/3] MedQuAD Dataset")
    print("=" * 70)
    try:
        download_medquad()
        results["MedQuAD"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] MedQuAD failed: {e}")
        results["MedQuAD"] = f"FAILED: {e}"

    # 2. FDA
    print("\n\n" + "=" * 70)
    print("  [2/3] FDA Drug Labels")
    print("=" * 70)
    try:
        download_fda()
        results["FDA"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] FDA failed: {e}")
        results["FDA"] = f"FAILED: {e}"

    # 3. MTSamples
    print("\n\n" + "=" * 70)
    print("  [3/3] MTSamples Medical Records")
    print("=" * 70)
    try:
        download_mtsamples()
        results["MTSamples"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] MTSamples failed: {e}")
        results["MTSamples"] = f"FAILED: {e}"

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
    print("\n  Next step: Run 'python scripts/build_vectorstore.py'")


if __name__ == "__main__":
    main()
