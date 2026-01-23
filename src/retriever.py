import chromadb
from .embeddings import embed_text
from .config import VECTORSTORE_PATH, DEFAULT_TOP_K

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


def retrieve(query: str, collection_name: str, top_k: int = 5) -> dict:
    """
    Retrieve relevant documents for a query.

    Args:
        query: User's question
        collection_name: Name of collection to search
        top_k: Number of results to return

    Returns:
        Dict with 'documents', 'metadatas', 'distances'
    """
    collection = get_or_create_collection(collection_name)
    query_embedding = embed_text(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return {
        "documents": results["documents"][0] if results["documents"] else [],
        "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        "distances": results["distances"][0] if results["distances"] else []
    }


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
