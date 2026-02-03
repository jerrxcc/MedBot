#!/usr/bin/env python3
"""
Unit Test Runner for MedBot RAG Optimization

This standalone script runs all unit tests without requiring pytest.
Run with: python tests/run_unit_tests.py
"""

import sys
import os
from pathlib import Path
import traceback
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.details = []

    def add_pass(self, name):
        self.passed += 1
        self.details.append(("PASS", name, None))
        print(f"  ✅ {name}")

    def add_fail(self, name, message):
        self.failed += 1
        self.details.append(("FAIL", name, message))
        print(f"  ❌ {name}")
        print(f"     {message}")

    def add_error(self, name, message):
        self.errors += 1
        self.details.append(("ERROR", name, message))
        print(f"  💥 {name}")
        print(f"     {message}")

    def summary(self):
        total = self.passed + self.failed + self.errors
        return f"Tests: {total} | Passed: {self.passed} | Failed: {self.failed} | Errors: {self.errors}"


def run_test(result: TestResult, name: str, test_func):
    """Run a single test and record result."""
    try:
        test_func()
        result.add_pass(name)
    except AssertionError as e:
        result.add_fail(name, str(e))
    except Exception as e:
        result.add_error(name, f"{type(e).__name__}: {e}")


# =============================================================================
# Phase 1.1: Config Module Tests
# =============================================================================

def test_config():
    """Run all config tests."""
    print("\n" + "=" * 60)
    print("Phase 1.1: Config Module Tests")
    print("=" * 60)
    result = TestResult()

    from src.config import (
        EMBEDDING_MODEL, EMBEDDING_DIM, DEFAULT_TOP_K, CHUNK_SIZE,
        BM25_WEIGHT, DENSE_WEIGHT, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
        CONFIDENCE_LOW, COLLECTIONS
    )

    def test_embedding_model():
        assert EMBEDDING_MODEL == "pritamdeka/S-PubMedBert-MS-MARCO", \
            f"Expected PubMedBERT model, got {EMBEDDING_MODEL}"

    def test_embedding_dim():
        assert EMBEDDING_DIM == 768, f"Expected 768, got {EMBEDDING_DIM}"

    def test_default_top_k():
        assert DEFAULT_TOP_K == 8, f"Expected 8, got {DEFAULT_TOP_K}"

    def test_chunk_size():
        assert CHUNK_SIZE == 800, f"Expected 800, got {CHUNK_SIZE}"

    def test_bm25_weight():
        assert BM25_WEIGHT == 0.3, f"Expected 0.3, got {BM25_WEIGHT}"

    def test_dense_weight():
        assert DENSE_WEIGHT == 0.7, f"Expected 0.7, got {DENSE_WEIGHT}"

    def test_confidence_thresholds():
        assert CONFIDENCE_HIGH == 0.7, f"Expected 0.7, got {CONFIDENCE_HIGH}"
        assert CONFIDENCE_MEDIUM == 0.4, f"Expected 0.4, got {CONFIDENCE_MEDIUM}"
        assert CONFIDENCE_LOW == 0.2, f"Expected 0.2, got {CONFIDENCE_LOW}"

    def test_collections():
        assert COLLECTIONS["symptoms"] == "medquad_symptoms"
        assert COLLECTIONS["medication"] == "fda_drugs"
        assert COLLECTIONS["records"] == "medical_records"

    run_test(result, "EMBEDDING_MODEL == PubMedBERT", test_embedding_model)
    run_test(result, "EMBEDDING_DIM == 768", test_embedding_dim)
    run_test(result, "DEFAULT_TOP_K == 8", test_default_top_k)
    run_test(result, "CHUNK_SIZE == 800", test_chunk_size)
    run_test(result, "BM25_WEIGHT == 0.3", test_bm25_weight)
    run_test(result, "DENSE_WEIGHT == 0.7", test_dense_weight)
    run_test(result, "Confidence thresholds correct", test_confidence_thresholds)
    run_test(result, "Collection names correct", test_collections)

    print(f"\n{result.summary()}")
    return result


# =============================================================================
# Phase 1.2: Embeddings Module Tests
# =============================================================================

def test_embeddings():
    """Run all embeddings tests."""
    print("\n" + "=" * 60)
    print("Phase 1.2: Embeddings Module Tests")
    print("=" * 60)
    result = TestResult()

    from src.embeddings import get_model, embed_text, embed_texts, get_embedding_dimension

    # Load model once
    print("  Loading embedding model...")
    model = get_model()
    print("  Model loaded successfully.")

    def test_model_loads():
        assert model is not None, "Model failed to load"

    def test_model_dimension():
        dim = model.get_sentence_embedding_dimension()
        assert dim == 768, f"Expected 768, got {dim}"

    def test_embed_text_length():
        vector = embed_text("test medical query")
        assert len(vector) == 768, f"Expected 768, got {len(vector)}"

    def test_embed_text_returns_list():
        vector = embed_text("test")
        assert isinstance(vector, list), f"Expected list, got {type(vector)}"

    def test_embed_texts_batch():
        texts = ["headache", "fever", "cough"]
        vectors = embed_texts(texts)
        assert len(vectors) == 3, f"Expected 3, got {len(vectors)}"
        for v in vectors:
            assert len(v) == 768, f"Expected 768-dim vectors"

    def test_get_embedding_dimension():
        dim = get_embedding_dimension()
        assert dim == 768, f"Expected 768, got {dim}"

    run_test(result, "Model loads successfully", test_model_loads)
    run_test(result, "Model dimension == 768", test_model_dimension)
    run_test(result, "embed_text() returns 768-dim vector", test_embed_text_length)
    run_test(result, "embed_text() returns list", test_embed_text_returns_list)
    run_test(result, "embed_texts() batch processing", test_embed_texts_batch)
    run_test(result, "get_embedding_dimension() == 768", test_get_embedding_dimension)

    print(f"\n{result.summary()}")
    return result


# =============================================================================
# Phase 1.3: Retriever Module Tests - Confidence Scoring
# =============================================================================

def test_confidence_scoring():
    """Run confidence scoring tests."""
    print("\n" + "=" * 60)
    print("Phase 1.3a: Confidence Scoring Tests")
    print("=" * 60)
    result = TestResult()

    from src.retriever import calculate_confidence

    def test_high_confidence():
        distances = [20, 22, 24]
        confidence, level = calculate_confidence(distances)
        assert level == "high", f"Expected 'high', got '{level}' (conf={confidence})"
        assert confidence >= 0.7, f"Expected >= 0.7, got {confidence}"

    def test_medium_confidence():
        distances = [30, 32, 34]
        confidence, level = calculate_confidence(distances)
        assert level == "medium", f"Expected 'medium', got '{level}' (conf={confidence})"
        assert 0.4 <= confidence < 0.7, f"Expected 0.4-0.7, got {confidence}"

    def test_low_confidence():
        distances = [38, 40, 42]
        confidence, level = calculate_confidence(distances)
        assert level in ["low", "very_low"], f"Expected low/very_low, got '{level}'"
        assert confidence < 0.4, f"Expected < 0.4, got {confidence}"

    def test_very_low_confidence():
        distances = [44, 46, 48]
        confidence, level = calculate_confidence(distances)
        assert level == "very_low", f"Expected 'very_low', got '{level}'"
        assert confidence < 0.2, f"Expected < 0.2, got {confidence}"

    def test_empty_distances():
        confidence, level = calculate_confidence([])
        assert confidence == 0.0, f"Expected 0.0, got {confidence}"
        assert level == "none", f"Expected 'none', got '{level}'"

    def test_confidence_bounds():
        conf1, _ = calculate_confidence([5, 6, 7])
        assert 0 <= conf1 <= 1, f"Out of bounds: {conf1}"
        conf2, _ = calculate_confidence([100, 110, 120])
        assert 0 <= conf2 <= 1, f"Out of bounds: {conf2}"

    run_test(result, "High confidence (distances ~20)", test_high_confidence)
    run_test(result, "Medium confidence (distances ~30)", test_medium_confidence)
    run_test(result, "Low confidence (distances ~40)", test_low_confidence)
    run_test(result, "Very low confidence (distances ~45+)", test_very_low_confidence)
    run_test(result, "Empty distances -> none", test_empty_distances)
    run_test(result, "Confidence always 0-1", test_confidence_bounds)

    print(f"\n{result.summary()}")
    return result


# =============================================================================
# Phase 1.3: Retriever Module Tests - Retrieval Functions
# =============================================================================

def test_retrieval():
    """Run retrieval function tests."""
    print("\n" + "=" * 60)
    print("Phase 1.3b: Retrieval Function Tests")
    print("=" * 60)
    result = TestResult()

    from src.retriever import retrieve_with_confidence, retrieve_with_fallback

    def test_retrieve_with_confidence_structure():
        res = retrieve_with_confidence("headache", "medquad_symptoms", top_k=3)
        assert "documents" in res, "Missing 'documents'"
        assert "confidence" in res, "Missing 'confidence'"
        assert "confidence_level" in res, "Missing 'confidence_level'"
        assert "collection" in res, "Missing 'collection'"

    def test_common_drug_query():
        res = retrieve_with_confidence("ibuprofen uses", "fda_drugs", top_k=5)
        assert res["confidence_level"] in ["high", "medium"], \
            f"Common query got {res['confidence_level']}"

    def test_fallback_structure():
        res = retrieve_with_fallback("headache", "medquad_symptoms", top_k=5)
        assert "fallback_used" in res, "Missing 'fallback_used'"
        assert isinstance(res["fallback_used"], bool)

    def test_fallback_not_triggered_for_high_conf():
        res = retrieve_with_fallback("aspirin side effects", "fda_drugs", top_k=5)
        if res["confidence_level"] in ["high", "medium"]:
            assert res["fallback_used"] == False, "Shouldn't use fallback for good confidence"

    run_test(result, "retrieve_with_confidence structure", test_retrieve_with_confidence_structure)
    run_test(result, "Common drug query -> high/medium confidence", test_common_drug_query)
    run_test(result, "retrieve_with_fallback structure", test_fallback_structure)
    run_test(result, "High confidence -> no fallback", test_fallback_not_triggered_for_high_conf)

    print(f"\n{result.summary()}")
    return result


# =============================================================================
# Phase 1.4: Hybrid Retriever Module Tests
# =============================================================================

def test_hybrid_retriever():
    """Run hybrid retriever tests."""
    print("\n" + "=" * 60)
    print("Phase 1.4: Hybrid Retriever Tests")
    print("=" * 60)
    result = TestResult()

    from src.hybrid_retriever import HybridRetriever, hybrid_retrieve

    retriever = HybridRetriever("medquad_symptoms")

    def test_initialization():
        assert retriever.collection_name == "medquad_symptoms"
        assert retriever._bm25 is None  # Lazy init

    def test_tokenize():
        tokens = retriever._tokenize("What is the treatment for headache?")
        assert isinstance(tokens, list)
        assert "headache" in tokens
        assert "treatment" in tokens
        assert all(t.islower() for t in tokens)

    def test_tokenize_medical_terms():
        tokens = retriever._tokenize("Ibuprofen 400mg for inflammation")
        assert "ibuprofen" in tokens
        assert "400mg" in tokens

    def test_search_bm25():
        results = retriever.search_bm25("headache treatment", top_k=5)
        assert isinstance(results, list)
        if results:
            assert "document" in results[0]
            assert results[0]["method"] == "bm25"

    def test_search_dense():
        results = retriever.search_dense("headache treatment", top_k=5)
        assert isinstance(results, list)
        if results:
            assert "document" in results[0]
            assert results[0]["method"] == "dense"

    def test_hybrid_search():
        results = retriever.search("headache symptoms", top_k=5)
        assert isinstance(results, list)
        if results:
            assert "rrf_score" in results[0]

    def test_hybrid_retrieve_function():
        res = hybrid_retrieve("fever", "medquad_symptoms", top_k=3)
        assert "documents" in res
        assert "metadatas" in res
        assert "distances" in res

    def test_get_documents_count():
        count = retriever.get_documents_count()
        assert isinstance(count, int)
        assert count >= 0

    run_test(result, "HybridRetriever initialization", test_initialization)
    run_test(result, "_tokenize() works correctly", test_tokenize)
    run_test(result, "_tokenize() preserves medical terms", test_tokenize_medical_terms)
    run_test(result, "search_bm25() returns results", test_search_bm25)
    run_test(result, "search_dense() returns results", test_search_dense)
    run_test(result, "search() returns fused results", test_hybrid_search)
    run_test(result, "hybrid_retrieve() convenience function", test_hybrid_retrieve_function)
    run_test(result, "get_documents_count()", test_get_documents_count)

    print(f"\n{result.summary()}")
    return result


# =============================================================================
# Data Validation Tests
# =============================================================================

def test_data_validation():
    """Run data validation tests."""
    print("\n" + "=" * 60)
    print("Data Validation Tests")
    print("=" * 60)
    result = TestResult()

    from src.retriever import get_or_create_collection

    def test_fda_drugs_count():
        coll = get_or_create_collection("fda_drugs")
        count = coll.count()
        print(f"     FDA drugs: {count} documents")
        assert count > 1500, f"Expected > 1500, got {count}"

    def test_medquad_symptoms_count():
        coll = get_or_create_collection("medquad_symptoms")
        count = coll.count()
        print(f"     MedQuAD symptoms: {count} documents")
        assert count > 30000, f"Expected > 30000, got {count}"

    def test_medical_records_exists():
        coll = get_or_create_collection("medical_records")
        count = coll.count()
        print(f"     Medical records: {count} documents")
        assert count > 0, "Medical records collection is empty"

    run_test(result, "FDA drugs > 1500 docs", test_fda_drugs_count)
    run_test(result, "MedQuAD symptoms > 30000 docs", test_medquad_symptoms_count)
    run_test(result, "Medical records exists", test_medical_records_exists)

    print(f"\n{result.summary()}")
    return result


# =============================================================================
# Integration Tests
# =============================================================================

def test_integration():
    """Run integration tests."""
    print("\n" + "=" * 60)
    print("Integration Tests")
    print("=" * 60)
    result = TestResult()

    from src.retriever import retrieve_with_fallback, format_context

    def test_symptom_pipeline():
        res = retrieve_with_fallback("I have a headache and feel dizzy", "medquad_symptoms")
        ctx = format_context(res)
        assert len(res["documents"]) > 0, "No documents retrieved"
        assert len(ctx) > 0, "Empty context"
        assert res["confidence"] > 0, "Zero confidence"

    def test_medication_pipeline():
        res = retrieve_with_fallback("What is ibuprofen used for?", "fda_drugs")
        ctx = format_context(res)
        assert len(res["documents"]) > 0, "No documents retrieved"
        assert len(ctx) > 0, "Empty context"

    run_test(result, "Symptom query full pipeline", test_symptom_pipeline)
    run_test(result, "Medication query full pipeline", test_medication_pipeline)

    print(f"\n{result.summary()}")
    return result


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all tests and print summary."""
    print("\n" + "=" * 60)
    print("MedBot RAG Optimization - Unit Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_results = []

    # Run test phases
    all_results.append(("Config Module", test_config()))
    all_results.append(("Embeddings Module", test_embeddings()))
    all_results.append(("Confidence Scoring", test_confidence_scoring()))
    all_results.append(("Retrieval Functions", test_retrieval()))
    all_results.append(("Hybrid Retriever", test_hybrid_retriever()))
    all_results.append(("Data Validation", test_data_validation()))
    all_results.append(("Integration", test_integration()))

    # Final Summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)

    total_passed = sum(r.passed for _, r in all_results)
    total_failed = sum(r.failed for _, r in all_results)
    total_errors = sum(r.errors for _, r in all_results)

    for name, r in all_results:
        status = "✅" if r.failed == 0 and r.errors == 0 else "❌"
        print(f"  {status} {name}: {r.summary()}")

    print("-" * 60)
    print(f"  TOTAL: Passed={total_passed} | Failed={total_failed} | Errors={total_errors}")

    if total_failed == 0 and total_errors == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_failed + total_errors} tests need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
