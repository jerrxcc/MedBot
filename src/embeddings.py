from sentence_transformers import SentenceTransformer
from .config import EMBEDDING_MODEL, EMBEDDING_DIM

# Load embedding model (lazy initialization)
_model = None


def get_model():
    """Get or initialize the embedding model."""
    global _model
    if _model is None:
        print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        actual_dim = _model.get_sentence_embedding_dimension()
        if actual_dim != EMBEDDING_DIM:
            print(f"[WARNING] Model dimension ({actual_dim}) differs from config ({EMBEDDING_DIM})")
    return _model


def embed_text(text: str) -> list:
    """
    Convert text to embedding vector.

    Args:
        text: Input text string

    Returns:
        Embedding vector as list (dimension depends on model)
    """
    model = get_model()
    embedding = model.encode(text)
    return embedding.tolist()


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
    """Get the actual embedding dimension from the loaded model."""
    model = get_model()
    return model.get_sentence_embedding_dimension()
