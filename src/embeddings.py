from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL

# Load embedding model
model = None


def get_model():
    """Get or initialize the embedding model."""
    global model
    if model is None:
        model = SentenceTransformer(EMBEDDING_MODEL)
    return model


def embed_text(text: str) -> list:
    """
    Convert text to embedding vector.

    Args:
        text: Input text string

    Returns:
        Embedding vector as list
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
    embeddings = model.encode(texts)
    return embeddings.tolist()
