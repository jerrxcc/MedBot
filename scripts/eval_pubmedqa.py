"""Evaluate retrieval quality on PubMedQA known-item retrieval (200 queries)."""

import json
import random
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retriever import retrieve

DATA_FILE = PROJECT_ROOT / "data" / "processed" / "pubmedqa.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "data" / "eval_results" / "pubmedqa_results.json"
COLLECTION_NAME = "pubmedqa"
NUM_QUERIES = 200
TOP_K = 10
SEED = 42


def load_labeled_queries():
    """Load PubMedQA labeled subset, group by PMID, pick question from first chunk."""
    pmid_to_question = {}
    with open(DATA_FILE) as f:
        for line in f:
            doc = json.loads(line)
            meta = doc.get("metadata", {})
            if meta.get("subset") != "pqa_labeled":
                continue
            pmid = meta.get("pmid", "")
            question = meta.get("question", "")
            if pmid and question and pmid not in pmid_to_question:
                pmid_to_question[pmid] = question
    return pmid_to_question


def evaluate():
    pmid_to_question = load_labeled_queries()
    print(f"[INFO] Found {len(pmid_to_question)} unique labeled PubMedQA PMIDs")

    random.seed(SEED)
    sampled_pmids = random.sample(sorted(pmid_to_question.keys()), min(NUM_QUERIES, len(pmid_to_question)))
    print(f"[INFO] Sampled {len(sampled_pmids)} queries for evaluation")

    recall_at = {1: 0, 3: 0, 5: 0, 10: 0}
    reciprocal_ranks = []
    per_query_results = []

    for i, pmid in enumerate(sampled_pmids):
        question = pmid_to_question[pmid]
        results = retrieve(question, COLLECTION_NAME, top_k=TOP_K)

        # Check which retrieved docs match the target PMID
        retrieved_pmids = [m.get("pmid", "") for m in results.get("metadatas", [])]
        rank = None
        for j, rp in enumerate(retrieved_pmids):
            if rp == pmid:
                rank = j + 1
                break

        rr = 1.0 / rank if rank else 0.0
        reciprocal_ranks.append(rr)

        for k in recall_at:
            if rank is not None and rank <= k:
                recall_at[k] += 1

        per_query_results.append({
            "pmid": pmid,
            "question": question,
            "rank": rank,
            "reciprocal_rank": rr,
            "retrieved_pmids": retrieved_pmids[:5],
        })

        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{len(sampled_pmids)}] processed")

    n = len(sampled_pmids)
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

    print(f"\n[RESULTS] PubMedQA Retrieval ({n} queries):")
    for k, v in metrics.items():
        if k not in ("collection", "num_queries"):
            print(f"  {k}: {v}")
    print(f"\nResults saved to {OUTPUT_FILE}")
    return metrics


if __name__ == "__main__":
    evaluate()
