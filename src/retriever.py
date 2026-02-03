import chromadb
from .embeddings import embed_text
from .llm import translate_to_english
from .config import (
    VECTORSTORE_PATH,
    DEFAULT_TOP_K,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
    ENABLE_CROSS_COLLECTION_FALLBACK,
    ALL_COLLECTIONS
)

# ChromaDB client (lazy initialization)
_client = None


def get_client():
    """Get or initialize ChromaDB client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(VECTORSTORE_PATH))
    return _client


def get_or_create_collection(name: str):
    """Get or create a collection by name."""
    client = get_client()
    return client.get_or_create_collection(name=name)


def add_documents(collection_name: str, documents: list, metadatas: list = None, ids: list = None):
    """
    Add documents to a collection.

    Args:
        collection_name: Name of the collection
        documents: List of document texts
        metadatas: Optional list of metadata dicts
        ids: Optional list of document IDs
    """
    collection = get_or_create_collection(collection_name)

    if ids is None:
        ids = [f"{collection_name}_{i}" for i in range(len(documents))]

    embeddings = [embed_text(doc) for doc in documents]

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )


from .translator import translate_query_for_retrieval

def retrieve(query: str, collection_name: str, top_k: int = 5) -> dict:
    """
    Retrieve relevant documents for a query.
    
    Args:
        query: User's question (will be translated if needed)
        collection_name: Name of collection to search
        top_k: Number of results to return

    Returns:
        Dict with 'documents', 'metadatas', 'distances'
    """
    collection = get_or_create_collection(collection_name)
    
    # Translate query for better matching with English database
    search_query = translate_query_for_retrieval(query)
    query_embedding = embed_text(search_query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return {
        "documents": results["documents"][0] if results["documents"] else [],
        "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        "distances": results["distances"][0] if results["distances"] else []
    }


def calculate_confidence(distances: list) -> tuple:
    """
    Calculate confidence score from retrieval distances.

    Args:
        distances: List of L2 distances from ChromaDB

    Returns:
        Tuple of (confidence_score, confidence_level)
        - confidence_score: float between 0 and 1
        - confidence_level: 'high', 'medium', 'low', 'very_low', or 'none'
    """
    if not distances:
        return 0.0, "none"

    # ChromaDB uses L2 distance: lower is better
    # For 768-dim embeddings (PubMedBERT), typical distances are:
    # - Very similar: 15-25
    # - Somewhat related: 25-35
    # - Unrelated: 35-50+
    min_distance = min(distances)
    avg_distance = sum(distances) / len(distances)

    # Convert distance to confidence (inverse relationship)
    # Scale for 768-dim embeddings: good results typically < 30
    combined_dist = 0.6 * min_distance + 0.4 * avg_distance

    # Normalize: 15 -> 1.0, 45 -> 0.0
    confidence = max(0, min(1, (45 - combined_dist) / 30))

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
    """
    Retrieve documents with confidence scoring.

    Args:
        query: User's question
        collection_name: Name of collection to search
        top_k: Number of results to return

    Returns:
        Dict with 'documents', 'metadatas', 'distances', 'confidence', 'confidence_level'
    """
    results = retrieve(query, collection_name, top_k)

    confidence, level = calculate_confidence(results.get("distances", []))

    return {
        **results,
        "confidence": confidence,
        "confidence_level": level,
        "collection": collection_name
    }


def retrieve_with_fallback(query: str, primary_collection: str, top_k: int = 5) -> dict:
    """
    Retrieve documents with cross-collection fallback when confidence is low.

    When the primary collection returns low-confidence results, this function
    searches all available collections and returns the best results.

    Args:
        query: User's question (can be in any language)
        primary_collection: Primary collection to search first
        top_k: Number of results to return

    Returns:
        Dict with results including 'fallback_used' flag and translation info
    """
    # Translate query to English for better retrieval
    # (knowledge base and embeddings are English-optimized)
    translated_query = translate_to_english(query)

    # First try primary collection with translated query
    results = retrieve_with_confidence(translated_query, primary_collection, top_k)

    # Store query translation info
    results["original_query"] = query
    results["translated_query"] = translated_query if translated_query != query else None

    # If confidence is acceptable or fallback is disabled, return primary results
    if not ENABLE_CROSS_COLLECTION_FALLBACK:
        results["fallback_used"] = False
        return results

    if results["confidence_level"] in ["high", "medium"]:
        results["fallback_used"] = False
        return results

    # Low confidence - try searching all collections
    all_results = []

    for coll_name in ALL_COLLECTIONS:
        try:
            coll_results = retrieve(translated_query, coll_name, top_k=3)
            for doc, dist, meta in zip(
                coll_results.get("documents", []),
                coll_results.get("distances", []),
                coll_results.get("metadatas", [])
            ):
                all_results.append({
                    "document": doc,
                    "distance": dist,
                    "metadata": {**meta, "from_collection": coll_name} if meta else {"from_collection": coll_name}
                })
        except Exception:
            # Skip collections that fail (might not exist yet)
            continue

    if not all_results:
        results["fallback_used"] = False
        return results

    # Sort by distance (lower is better) and take top_k
    all_results.sort(key=lambda x: x["distance"])
    top_results = all_results[:top_k]

    # Recalculate confidence with new results
    new_distances = [r["distance"] for r in top_results]
    new_confidence, new_level = calculate_confidence(new_distances)

    # Only use fallback if it actually improves confidence
    if new_confidence > results["confidence"]:
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
            "translated_query": translated_query if translated_query != query else None
        }

    results["fallback_used"] = False
    return results


def format_context(results: dict) -> str:
    """
    Format retrieved results into context string.

    Args:
        results: Dict from retrieve()

    Returns:
        Formatted context string with sources
    """
    if not results["documents"]:
        return ""

    context_parts = []
    for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"]), 1):
        source = meta.get("source", "Unknown") if meta else "Unknown"
        context_parts.append(f"[{i}] (Source: {source})\n{doc}")

    return "\n\n".join(context_parts)
