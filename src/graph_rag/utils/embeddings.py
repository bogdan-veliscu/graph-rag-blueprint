"""Embedding utilities."""

from typing import List

from sentence_transformers import SentenceTransformer

from src.graph_rag.config import config

# Global model instance
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """Get or create embedding model instance.

    Returns:
        SentenceTransformer model
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(config.embedding_model)
    return _embedding_model


def embed_text(text: str) -> List[float]:
    """Embed a single text.

    Args:
        text: Text to embed

    Returns:
        Embedding vector
    """
    model = get_embedding_model()
    return model.encode(text, show_progress_bar=False).tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts.

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    return model.encode(texts, show_progress_bar=False).tolist()

