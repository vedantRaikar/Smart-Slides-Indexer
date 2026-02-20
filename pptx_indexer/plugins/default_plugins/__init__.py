"""Default plugins initialization."""
from .implementations import (
    OpenAILLM,
    SentenceTransformerEmbedder,
    ChromaVectorStore,
    PytesseractOCR,
)

__all__ = [
    "OpenAILLM",
    "SentenceTransformerEmbedder",
    "ChromaVectorStore",
    "PytesseractOCR",
]
