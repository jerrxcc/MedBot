"""
Hybrid Retriever combining BM25 (lexical) and Dense (semantic) search.

Uses Reciprocal Rank Fusion (RRF) to combine results from both methods
for improved retrieval quality, especially for medical terminology.

Status: EXPERIMENTAL

This module is intentionally not wired into the default UIs (Chainlit/Gradio/CLI).
The production retrieval path is `src/retriever.py`, which provides:
- confidence scoring based on vector distances
- cross-collection fallback across `ALL_COLLECTIONS`

Important tradeoff:
BM25 indexing here loads *all* documents from a Chroma collection into memory
to build an in-memory BM25 index. This is not suitable for very large
collections (for example `pubmedqa`) in an interactive UI request path.
"""

import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import chromadb

from .embeddings import embed_text
from .config import (
    VECTORSTORE_PATH,
    BM25_WEIGHT,
    DENSE_WEIGHT,
    RRF_K,
    DEFAULT_TOP_K
)


class HybridRetriever:
    """
    Hybrid retriever combining BM25 and Dense vector search.

    Architecture:
        User Query
            |
        +---+---+
        |       |
      BM25    Dense
     Top-N   Top-N
        |       |
        +---+---+
            |
          RRF Fusion
            |
         Top-K Results
    """

    def __init__(self, collection_name: str):
        """
        Initialize hybrid retriever for a specific collection.

        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._documents = None
        self._doc_ids = None
        self._metadatas = None
        self._bm25 = None
        self._tokenized_corpus = None

    def _get_client(self):
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(path=str(VECTORSTORE_PATH))
        return self._client

    def _get_collection(self):
        """Get or initialize the ChromaDB collection."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(self.collection_name)
        return self._collection

    def _load_documents(self):
        """Load all documents from collection for BM25 indexing."""
        if self._documents is not None:
            return

        collection = self._get_collection()
        count = collection.count()

        if count == 0:
            self._documents = []
            self._doc_ids = []
            self._metadatas = []
            return

        # Fetch all documents
        results = collection.get(
            include=["documents", "metadatas"]
        )

        self._documents = results.get("documents", [])
        self._doc_ids = results.get("ids", [])
        self._metadatas = results.get("metadatas", [])

    def _build_bm25_index(self):
        """Build BM25 index from documents."""
        if self._bm25 is not None:
            return

        self._load_documents()

        if not self._documents:
            return

        # Tokenize documents for BM25
        self._tokenized_corpus = [self._tokenize(doc) for doc in self._documents]
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.

        Uses simple whitespace + punctuation tokenization with lowercasing.
        Preserves medical terms and numbers.
        """
        # Lowercase and split on non-alphanumeric characters
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def search_bm25(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Perform BM25 lexical search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of dicts with 'doc_id', 'document', 'metadata', 'score'
        """
        self._build_bm25_index()

        if not self._bm25 or not self._documents:
            return []

        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        # Get top-k indices sorted by score descending
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include documents with positive BM25 score
                results.append({
                    "doc_id": self._doc_ids[idx],
                    "document": self._documents[idx],
                    "metadata": self._metadatas[idx] if self._metadatas else {},
                    "score": float(scores[idx]),
                    "method": "bm25"
                })

        return results

    def search_dense(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Perform dense vector (semantic) search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of dicts with 'doc_id', 'document', 'metadata', 'score'
        """
        collection = self._get_collection()

        if collection.count() == 0:
            return []

        query_embedding = embed_text(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        output = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            ids = results["ids"][0]
            metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0] * len(docs)

            for doc_id, doc, meta, dist in zip(ids, docs, metadatas, distances):
                # Convert L2 distance to similarity score (higher is better)
                # L2 distance ranges from 0 (identical) to ~4 (very different)
                similarity = max(0, 1 - (dist / 2))
                output.append({
                    "doc_id": doc_id,
                    "document": doc,
                    "metadata": meta,
                    "score": similarity,
                    "distance": dist,
                    "method": "dense"
                })

        return output

    def search(
        self,
        query: str,
        top_k: int = None,
        bm25_weight: float = None,
        dense_weight: float = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining BM25 and Dense results using RRF.

        Args:
            query: Search query
            top_k: Number of final results to return
            bm25_weight: Weight for BM25 results (default from config)
            dense_weight: Weight for Dense results (default from config)

        Returns:
            List of dicts with merged results, sorted by RRF score
        """
        top_k = top_k or DEFAULT_TOP_K
        bm25_weight = bm25_weight if bm25_weight is not None else BM25_WEIGHT
        dense_weight = dense_weight if dense_weight is not None else DENSE_WEIGHT

        # Get more results than needed for fusion
        fetch_k = top_k * 3

        # Get results from both methods
        bm25_results = self.search_bm25(query, top_k=fetch_k)
        dense_results = self.search_dense(query, top_k=fetch_k)

        # Calculate RRF scores
        rrf_scores = {}
        doc_data = {}

        # Process BM25 results
        for rank, result in enumerate(bm25_results):
            doc_id = result["doc_id"]
            rrf_score = bm25_weight / (RRF_K + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = result

        # Process Dense results
        for rank, result in enumerate(dense_results):
            doc_id = result["doc_id"]
            rrf_score = dense_weight / (RRF_K + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = result

        # Sort by RRF score and take top_k
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]

        results = []
        for doc_id in sorted_ids:
            data = doc_data[doc_id]
            data["rrf_score"] = rrf_scores[doc_id]
            results.append(data)

        return results

    def get_documents_count(self) -> int:
        """Get the number of documents in the collection."""
        collection = self._get_collection()
        return collection.count()


def hybrid_retrieve(
    query: str,
    collection_name: str,
    top_k: int = None
) -> Dict[str, Any]:
    """
    Convenience function for hybrid retrieval.

    Args:
        query: Search query
        collection_name: Name of the collection to search
        top_k: Number of results

    Returns:
        Dict compatible with existing retriever interface
    """
    retriever = HybridRetriever(collection_name)
    results = retriever.search(query, top_k=top_k or DEFAULT_TOP_K)

    # Convert to existing format for compatibility
    return {
        "documents": [r["document"] for r in results],
        "metadatas": [r["metadata"] for r in results],
        "distances": [r.get("distance", 1 - r.get("rrf_score", 0)) for r in results],
        "scores": [r.get("rrf_score", r.get("score", 0)) for r in results],
        "methods": [r.get("method", "hybrid") for r in results]
    }
