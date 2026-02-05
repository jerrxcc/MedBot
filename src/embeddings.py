import torch
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from .config import EMBEDDING_MODEL

# Load embedding model (lazy initialization)
_model = None


def _get_device():
    """Detect best available device for inference."""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"  # Apple Silicon GPU
    return "cpu"


def get_model():
    """Get or initialize the embedding model."""
    global _model
    if _model is None:
        device = _get_device()
        print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL}")
        print(f"[INFO] Using device: {device}")
        _model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    return _model


@lru_cache(maxsize=256)
def _embed_text_cached(text: str) -> tuple:
    """Cache embeddings for repeated queries to reduce latency."""
    model = get_model()
    embedding = model.encode(text)
    return tuple(float(x) for x in embedding.tolist())


def embed_text(text: str) -> list:
    """
    Convert text to embedding vector.

    Args:
        text: Input text string

    Returns:
        Embedding vector as list
    """
    return list(_embed_text_cached(text))


def embed_texts(texts: list) -> list:
    """
    Convert multiple texts to embedding vectors.

    Args:
        texts: List of text strings

    Returns:
        List of embedding vectors
    """
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=len(texts) > 100)
    return embeddings.tolist()


def get_embedding_dimension() -> int:
    """
    Get the actual embedding dimension from the loaded model.

    Returns:
        Embedding dimension (e.g., 768 for PubMedBERT)
    """
    model = get_model()
    return model.get_sentence_embedding_dimension()
