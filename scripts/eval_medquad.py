"""Evaluate retrieval quality on MedQuAD condition retrieval (100 queries)."""

import json
import random
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retriever import retrieve

DATA_FILE = PROJECT_ROOT / "data" / "processed" / "symptoms.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "data" / "eval_results" / "medquad_results.json"
COLLECTION_NAME = "medquad_symptoms"
NUM_QUERIES = 100
TOP_K = 10
SEED = 42


def load_conditions():
    """Load unique condition names from MedQuAD symptoms data."""
    conditions = set()
    with open(DATA_FILE) as f:
        for line in f:
            doc = json.loads(line)
            condition = doc.get("metadata", {}).get("condition", "")
            if condition:
                conditions.add(condition)
    return sorted(conditions)


def evaluate():
    conditions = load_conditions()
    print(f"[INFO] Found {len(conditions)} unique conditions in MedQuAD")

    random.seed(SEED)
    sampled = random.sample(conditions, min(NUM_QUERIES, len(conditions)))
    print(f"[INFO] Sampled {len(sampled)} conditions for evaluation")

    recall_at = {1: 0, 3: 0, 5: 0, 10: 0}
    reciprocal_ranks = []
    per_query_results = []

    for i, condition in enumerate(sampled):
        results = retrieve(condition, COLLECTION_NAME, top_k=TOP_K)

        # Check which retrieved docs match the target condition
        retrieved_conditions = [m.get("condition", "") for m in results.get("metadatas", [])]
        rank = None
        for j, rc in enumerate(retrieved_conditions):
            if rc == condition:
                rank = j + 1
                break

        rr = 1.0 / rank if rank else 0.0
        reciprocal_ranks.append(rr)

        for k in recall_at:
            if rank is not None and rank <= k:
                recall_at[k] += 1

        per_query_results.append({
            "condition": condition,
            "rank": rank,
            "reciprocal_rank": rr,
            "retrieved_conditions": retrieved_conditions[:5],
        })

        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(sampled)}] processed")

    n = len(sampled)
    metrics = {
        "collection": COLLECTION_NAME,
        "num_queries": n,
        "recall_at_1": round(recall_at[1] / n, 4),
        "recall_at_3": round(recall_at[3] / n, 4),
        "recall_at_5": round(recall_at[5] / n, 4),
        "recall_at_10": round(recall_at[10] / n, 4),
        "mrr": round(sum(reciprocal_ranks) / n, 4),
    }

    output = {"metrics": metrics, "per_query": per_query_results}
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n[RESULTS] MedQuAD Retrieval ({n} queries):")
    for k, v in metrics.items():
        if k not in ("collection", "num_queries"):
            print(f"  {k}: {v}")
    print(f"\nResults saved to {OUTPUT_FILE}")
    return metrics


if __name__ == "__main__":
    evaluate()
