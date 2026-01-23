from sentence_transformers import SentenceTransformer

# Load embedding model
MODEL_NAME = "all-MiniLM-L6-v2"
model = None


def get_model():
    """Get or initialize the embedding model."""
    global model
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    return model


def embed_text(text: str) -> list:
    """
    Convert text to embedding vector.

    Args:
        text: Input text string

    Returns:
        384-dimensional embedding as list
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
        List of 384-dimensional embeddings
    """
    model = get_model()
    embeddings = model.encode(texts)
    return embeddings.tolist()
