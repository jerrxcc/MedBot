"""Vector store retrieval with confidence scoring and fallback support."""
import chromadb

from .config import (
    ALL_COLLECTIONS,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    ENABLE_CROSS_COLLECTION_FALLBACK,
    VECTORSTORE_PATH,
)
from .embeddings import embed_text
from .translator import translate_query_for_retrieval

_client = None


def get_client():
    """Get or initialize ChromaDB client (lazy loading)."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(VECTORSTORE_PATH))
    return _client


def get_or_create_collection(name: str):
    """Get or create a collection by name."""
    return get_client().get_or_create_collection(name=name)


def add_documents(collection_name: str, documents: list, metadatas: list = None, ids: list = None):
    """Add documents to a collection."""
    collection = get_or_create_collection(collection_name)
    ids = ids or [f"{collection_name}_{i}" for i in range(len(documents))]
    embeddings = [embed_text(doc) for doc in documents]

    collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)


def retrieve(query: str, collection_name: str, top_k: int = 5) -> dict:
    """Retrieve relevant documents for a query."""
    collection = get_or_create_collection(collection_name)
    results = collection.query(query_embeddings=[embed_text(query)], n_results=top_k)

    return {
        "documents": results["documents"][0] if results["documents"] else [],
        "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        "distances": results["distances"][0] if results["distances"] else [],
    }


def distance_to_relevance(distance: float) -> float:
    """
    Convert L2 distance to relevance percentage (0-100).

    For 768-dim embeddings: 15-25 = high, 25-35 = medium, 35-50+ = low
    """
    relevance = max(0, min(100, (50 - distance) / 30 * 100))
    return round(relevance, 1)


def calculate_confidence(distances: list) -> tuple[float, str]:
    """
    Calculate confidence score from retrieval distances.

    Returns tuple of (confidence_score 0-1, confidence_level string).
    """
    if not distances:
        return 0.0, "none"

    # Weighted combination of min and average distance
    min_dist = min(distances)
    avg_dist = sum(distances) / len(distances)
    combined_dist = 0.6 * min_dist + 0.4 * avg_dist

    # Convert to confidence score (lower distance = higher confidence)
    confidence = max(0, min(1, (50 - combined_dist) / 30))

    # Determine confidence level
    if confidence >= CONFIDENCE_HIGH:
        level = "high"
    elif confidence >= CONFIDENCE_MEDIUM:
        level = "medium"
    elif confidence >= CONFIDENCE_LOW:
        level = "low"
    else:
        level = "very_low"

    return round(confidence, 3), level


def retrieve_with_confidence(query: str, collection_name: str, top_k: int = 5) -> dict:
    """Retrieve documents with confidence scoring."""
    results = retrieve(query, collection_name, top_k)
    confidence, level = calculate_confidence(results.get("distances", []))

    return {
        **results,
        "confidence": confidence,
        "confidence_level": level,
        "collection": collection_name,
    }


def retrieve_with_fallback(query: str, primary_collection: str, top_k: int = 5) -> dict:
    """
    Retrieve documents with cross-collection fallback when confidence is low.

    Translates non-English queries and searches across collections if needed.
    """
    translated_query = translate_query_for_retrieval(query)
    results = retrieve_with_confidence(translated_query, primary_collection, top_k)

    results["original_query"] = query
    results["translated_query"] = translated_query if translated_query != query else None
    results["fallback_used"] = False

    # Return early if fallback disabled or confidence is acceptable
    if not ENABLE_CROSS_COLLECTION_FALLBACK:
        return results
    if results["confidence_level"] in ["high", "medium"]:
        return results

    # Low confidence - search all collections
    all_results = _search_all_collections(translated_query, top_k=3)
    if not all_results:
        return results

    # Sort by distance and take top_k
    all_results.sort(key=lambda x: x["distance"])
    top_results = all_results[:top_k]

    new_distances = [r["distance"] for r in top_results]
    new_confidence, new_level = calculate_confidence(new_distances)

    # Only use fallback if it improves confidence
    if new_confidence <= results["confidence"]:
        return results

    return {
        "documents": [r["document"] for r in top_results],
        "metadatas": [r["metadata"] for r in top_results],
        "distances": new_distances,
        "confidence": new_confidence,
        "confidence_level": new_level,
        "collection": "mixed",
        "fallback_used": True,
        "original_collection": primary_collection,
        "original_confidence": results["confidence"],
        "original_query": query,
        "translated_query": translated_query if translated_query != query else None,
    }


def _search_all_collections(query: str, top_k: int = 3) -> list:
    """Search all collections and return combined results."""
    all_results = []

    for coll_name in ALL_COLLECTIONS:
        try:
            coll_results = retrieve(query, coll_name, top_k=top_k)
            for doc, dist, meta in zip(
                coll_results.get("documents", []),
                coll_results.get("distances", []),
                coll_results.get("metadatas", [])
            ):
                metadata = {**(meta or {}), "from_collection": coll_name}
                all_results.append({"document": doc, "distance": dist, "metadata": metadata})
        except Exception:
            continue

    return all_results


def format_context(results: dict) -> str:
    """Format retrieved results into context string with sources."""
    if not results["documents"]:
        return ""

    parts = []
    for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"]), 1):
        source = (meta or {}).get("source", "Unknown")
        parts.append(f"[{i}] (Source: {source})\n{doc}")

    return "\n\n".join(parts)
