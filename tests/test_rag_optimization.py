"""
Comprehensive Test Suite for MedBot RAG Optimization

Tests cover:
1. Config module - all new configuration values
2. Embeddings module - PubMedBERT model, dimensions
3. Retriever module - confidence scoring, fallback logic
4. Hybrid retriever module - BM25 + Dense search

Run with: python -m pytest tests/test_rag_optimization.py -v
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Phase 1.1: Config Module Tests
# =============================================================================

class TestConfigModule:
    """Test configuration values are correctly set."""

    def test_embedding_model_name(self):
        """Verify correct embedding model is configured."""
        from src.config import EMBEDDING_MODEL
        assert EMBEDDING_MODEL == "pritamdeka/S-PubMedBert-MS-MARCO", \
            f"Expected PubMedBERT model, got {EMBEDDING_MODEL}"

    def test_embedding_dimension(self):
        """Verify embedding dimension is 768."""
        from src.config import EMBEDDING_DIM
        assert EMBEDDING_DIM == 768, f"Expected 768, got {EMBEDDING_DIM}"

    def test_default_top_k(self):
        """Verify default top_k is 8."""
        from src.config import DEFAULT_TOP_K
        assert DEFAULT_TOP_K == 8, f"Expected 8, got {DEFAULT_TOP_K}"

    def test_chunk_size(self):
        """Verify chunk size is 800."""
        from src.config import CHUNK_SIZE
        assert CHUNK_SIZE == 800, f"Expected 800, got {CHUNK_SIZE}"

    def test_bm25_weight(self):
        """Verify BM25 weight is 0.3."""
        from src.config import BM25_WEIGHT
        assert BM25_WEIGHT == 0.3, f"Expected 0.3, got {BM25_WEIGHT}"

    def test_dense_weight(self):
        """Verify dense weight is 0.7."""
        from src.config import DENSE_WEIGHT
        assert DENSE_WEIGHT == 0.7, f"Expected 0.7, got {DENSE_WEIGHT}"

    def test_confidence_thresholds(self):
        """Verify confidence thresholds are correctly set."""
        from src.config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW
        assert CONFIDENCE_HIGH == 0.7, f"Expected 0.7, got {CONFIDENCE_HIGH}"
        assert CONFIDENCE_MEDIUM == 0.4, f"Expected 0.4, got {CONFIDENCE_MEDIUM}"
        assert CONFIDENCE_LOW == 0.2, f"Expected 0.2, got {CONFIDENCE_LOW}"

    def test_collection_names(self):
        """Verify collection names are correctly configured."""
        from src.config import COLLECTIONS
        assert COLLECTIONS["symptoms"] == "medquad_symptoms"
        assert COLLECTIONS["medication"] == "fda_drugs"
        assert COLLECTIONS["records"] == "medical_records"


# =============================================================================
# Phase 1.2: Embeddings Module Tests
# =============================================================================

class TestEmbeddingsModule:
    """Test embedding model functionality."""

    @pytest.fixture(scope="class")
    def embedding_model(self):
        """Load the embedding model once for all tests in this class."""
        from src.embeddings import get_model
        return get_model()

    def test_model_loads_successfully(self, embedding_model):
        """Verify model loads without errors."""
        assert embedding_model is not None, "Model failed to load"

    def test_model_dimension(self, embedding_model):
        """Verify model outputs 768-dimensional vectors."""
        dim = embedding_model.get_sentence_embedding_dimension()
        assert dim == 768, f"Expected 768, got {dim}"

    def test_embed_text_returns_correct_length(self):
        """Test embed_text returns vector of correct length."""
        from src.embeddings import embed_text
        vector = embed_text("test medical query")
        assert len(vector) == 768, f"Expected 768, got {len(vector)}"

    def test_embed_text_returns_list(self):
        """Test embed_text returns a list."""
        from src.embeddings import embed_text
        vector = embed_text("test")
        assert isinstance(vector, list), f"Expected list, got {type(vector)}"

    def test_embed_texts_batch_processing(self):
        """Test embed_texts processes multiple texts correctly."""
        from src.embeddings import embed_texts
        texts = ["headache", "fever", "cough"]
        vectors = embed_texts(texts)
        assert len(vectors) == 3, f"Expected 3 vectors, got {len(vectors)}"
        for v in vectors:
            assert len(v) == 768, f"Expected 768-dim vectors"

    def test_get_embedding_dimension(self):
        """Test get_embedding_dimension helper function."""
        from src.embeddings import get_embedding_dimension
        dim = get_embedding_dimension()
        assert dim == 768, f"Expected 768, got {dim}"


# =============================================================================
# Phase 1.3: Retriever Module Tests - Confidence Scoring
# =============================================================================

class TestConfidenceScoring:
    """Test confidence calculation from distances."""

    def test_high_confidence_distances(self):
        """Test high confidence when distances are low (good matches)."""
        from src.retriever import calculate_confidence
        # Distances around 20-22 should give high confidence
        distances = [20, 22, 24]
        confidence, level = calculate_confidence(distances)
        assert level == "high", f"Expected 'high', got '{level}' (confidence={confidence})"
        assert confidence >= 0.7, f"Expected confidence >= 0.7, got {confidence}"

    def test_medium_confidence_distances(self):
        """Test medium confidence with moderate distances."""
        from src.retriever import calculate_confidence
        # Distances around 30-32 should give medium confidence
        distances = [30, 32, 34]
        confidence, level = calculate_confidence(distances)
        assert level == "medium", f"Expected 'medium', got '{level}' (confidence={confidence})"
        assert 0.4 <= confidence < 0.7, f"Expected 0.4 <= confidence < 0.7, got {confidence}"

    def test_low_confidence_distances(self):
        """Test low confidence with higher distances."""
        from src.retriever import calculate_confidence
        # Distances around 38-40 should give low confidence
        distances = [38, 40, 42]
        confidence, level = calculate_confidence(distances)
        assert level in ["low", "very_low"], f"Expected 'low' or 'very_low', got '{level}'"
        assert confidence < 0.4, f"Expected confidence < 0.4, got {confidence}"

    def test_very_low_confidence_distances(self):
        """Test very low confidence with high distances."""
        from src.retriever import calculate_confidence
        # Distances > 44 should give very low confidence
        distances = [44, 46, 48]
        confidence, level = calculate_confidence(distances)
        assert level == "very_low", f"Expected 'very_low', got '{level}' (confidence={confidence})"
        assert confidence < 0.2, f"Expected confidence < 0.2, got {confidence}"

    def test_empty_distances(self):
        """Test confidence is 0 with empty distances."""
        from src.retriever import calculate_confidence
        confidence, level = calculate_confidence([])
        assert confidence == 0.0, f"Expected 0.0, got {confidence}"
        assert level == "none", f"Expected 'none', got '{level}'"

    def test_confidence_bounds(self):
        """Test confidence is always between 0 and 1."""
        from src.retriever import calculate_confidence
        # Very low distances
        conf1, _ = calculate_confidence([5, 6, 7])
        assert 0 <= conf1 <= 1, f"Confidence out of bounds: {conf1}"

        # Very high distances
        conf2, _ = calculate_confidence([100, 110, 120])
        assert 0 <= conf2 <= 1, f"Confidence out of bounds: {conf2}"


# =============================================================================
# Phase 1.3: Retriever Module Tests - Retrieval with Confidence
# =============================================================================

class TestRetrieveWithConfidence:
    """Test retrieval functions with confidence scoring."""

    def test_retrieve_with_confidence_structure(self):
        """Test retrieve_with_confidence returns expected fields."""
        from src.retriever import retrieve_with_confidence
        result = retrieve_with_confidence("headache", "medquad_symptoms", top_k=3)

        # Check required fields exist
        assert "documents" in result
        assert "metadatas" in result
        assert "distances" in result
        assert "confidence" in result
        assert "confidence_level" in result
        assert "collection" in result

    def test_common_drug_query_confidence(self):
        """Test that common drug queries return high/medium confidence."""
        from src.retriever import retrieve_with_confidence
        result = retrieve_with_confidence("ibuprofen uses", "fda_drugs", top_k=5)

        assert result["confidence_level"] in ["high", "medium"], \
            f"Common drug query should have high/medium confidence, got {result['confidence_level']}"

    def test_rare_query_confidence(self):
        """Test that rare/unusual queries may return lower confidence."""
        from src.retriever import retrieve_with_confidence
        result = retrieve_with_confidence(
            "extremely rare xyz syndrome treatment with medication abc123",
            "medquad_symptoms",
            top_k=5
        )

        # This query likely won't match well, should not be high confidence
        # (it may still be medium depending on data, so we just check it runs)
        assert result["confidence"] >= 0
        assert result["confidence_level"] in ["high", "medium", "low", "very_low", "none"]


# =============================================================================
# Phase 1.3: Retriever Module Tests - Fallback Logic
# =============================================================================

class TestRetrieveWithFallback:
    """Test cross-collection fallback functionality."""

    def test_fallback_returns_expected_fields(self):
        """Test retrieve_with_fallback returns all expected fields."""
        from src.retriever import retrieve_with_fallback
        result = retrieve_with_fallback("headache", "medquad_symptoms", top_k=5)

        assert "documents" in result
        assert "metadatas" in result
        assert "distances" in result
        assert "confidence" in result
        assert "confidence_level" in result
        assert "fallback_used" in result

    def test_high_confidence_no_fallback(self):
        """Test that high confidence queries don't trigger fallback."""
        from src.retriever import retrieve_with_fallback
        result = retrieve_with_fallback("ibuprofen side effects", "fda_drugs", top_k=5)

        # Common query should have good confidence and not need fallback
        # (fallback_used should be False if confidence is already good)
        if result["confidence_level"] in ["high", "medium"]:
            assert result["fallback_used"] == False, \
                "High/medium confidence should not trigger fallback"

    def test_fallback_used_flag_exists(self):
        """Test fallback_used flag is always present."""
        from src.retriever import retrieve_with_fallback
        result = retrieve_with_fallback("test query", "medquad_symptoms", top_k=3)
        assert "fallback_used" in result
        assert isinstance(result["fallback_used"], bool)


# =============================================================================
# Phase 1.4: Hybrid Retriever Module Tests
# =============================================================================

class TestHybridRetriever:
    """Test hybrid BM25 + Dense retriever."""

    @pytest.fixture
    def retriever(self):
        """Create a hybrid retriever instance."""
        from src.hybrid_retriever import HybridRetriever
        return HybridRetriever("medquad_symptoms")

    def test_hybrid_retriever_initialization(self, retriever):
        """Test HybridRetriever initializes correctly."""
        assert retriever.collection_name == "medquad_symptoms"
        assert retriever._bm25 is None  # Lazy initialization

    def test_tokenize_method(self, retriever):
        """Test tokenization works correctly."""
        tokens = retriever._tokenize("What is the treatment for headache?")
        assert isinstance(tokens, list)
        assert "headache" in tokens
        assert "treatment" in tokens
        assert all(t.islower() for t in tokens)  # Should be lowercased

    def test_tokenize_preserves_medical_terms(self, retriever):
        """Test tokenization preserves medical terminology."""
        tokens = retriever._tokenize("Ibuprofen 400mg for inflammation")
        assert "ibuprofen" in tokens
        assert "400mg" in tokens
        assert "inflammation" in tokens

    def test_search_bm25_returns_results(self, retriever):
        """Test BM25 search returns results."""
        results = retriever.search_bm25("headache treatment", top_k=5)
        # Should return list (may be empty if collection is empty)
        assert isinstance(results, list)
        if results:
            assert "document" in results[0]
            assert "score" in results[0]
            assert results[0]["method"] == "bm25"

    def test_search_dense_returns_results(self, retriever):
        """Test dense search returns results."""
        results = retriever.search_dense("headache treatment", top_k=5)
        assert isinstance(results, list)
        if results:
            assert "document" in results[0]
            assert "score" in results[0]
            assert results[0]["method"] == "dense"

    def test_hybrid_search_returns_fused_results(self, retriever):
        """Test hybrid search combines BM25 and dense results."""
        results = retriever.search("headache symptoms", top_k=5)
        assert isinstance(results, list)
        if results:
            # Should have RRF score from fusion
            assert "rrf_score" in results[0]

    def test_hybrid_retrieve_convenience_function(self):
        """Test the hybrid_retrieve convenience function."""
        from src.hybrid_retriever import hybrid_retrieve
        result = hybrid_retrieve("fever", "medquad_symptoms", top_k=3)

        # Should match existing retriever interface
        assert "documents" in result
        assert "metadatas" in result
        assert "distances" in result

    def test_get_documents_count(self, retriever):
        """Test getting document count from collection."""
        count = retriever.get_documents_count()
        assert isinstance(count, int)
        assert count >= 0


# =============================================================================
# Data Validation Tests
# =============================================================================

class TestDataValidation:
    """Verify data collection sizes and integrity."""

    def test_fda_drugs_collection_size(self):
        """Verify FDA drugs collection has > 1500 documents."""
        from src.retriever import get_or_create_collection
        collection = get_or_create_collection("fda_drugs")
        count = collection.count()
        assert count > 1500, f"Expected > 1500 FDA drugs, got {count}"
        print(f"FDA drugs collection: {count} documents")

    def test_medquad_symptoms_collection_size(self):
        """Verify MedQuAD symptoms collection has > 30000 documents."""
        from src.retriever import get_or_create_collection
        collection = get_or_create_collection("medquad_symptoms")
        count = collection.count()
        assert count > 30000, f"Expected > 30000 symptoms, got {count}"
        print(f"MedQuAD symptoms collection: {count} documents")

    def test_medical_records_collection_exists(self):
        """Verify medical records collection exists."""
        from src.retriever import get_or_create_collection
        collection = get_or_create_collection("medical_records")
        count = collection.count()
        assert count > 0, "Medical records collection is empty"
        print(f"Medical records collection: {count} documents")


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_symptom_query_full_pipeline(self):
        """Test full symptom query pipeline."""
        from src.retriever import retrieve_with_fallback, format_context

        result = retrieve_with_fallback("I have a headache and feel dizzy", "medquad_symptoms")
        context = format_context(result)

        assert len(result["documents"]) > 0, "Should retrieve documents"
        assert len(context) > 0, "Should generate context"
        assert result["confidence"] > 0, "Should have positive confidence"

    def test_medication_query_full_pipeline(self):
        """Test full medication query pipeline."""
        from src.retriever import retrieve_with_fallback, format_context

        result = retrieve_with_fallback("What is ibuprofen used for?", "fda_drugs")
        context = format_context(result)

        assert len(result["documents"]) > 0, "Should retrieve drug info"
        assert len(context) > 0, "Should generate context"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-x"])
