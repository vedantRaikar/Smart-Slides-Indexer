"""Default plugins initialization."""

from .implementations import (
    ChromaVectorStore,
    GeminiLLM,
    OpenAILLM,
    PytesseractOCR,
    SentenceTransformerEmbedder,
    PaddleOCR,
    GroqLLM,
    BigPickleLLM,
)

__all__ = [
    "OpenAILLM",
    "GeminiLLM",
    "SentenceTransformerEmbedder",
    "ChromaVectorStore",
    "PytesseractOCR",
    'PaddleOCR',
    'GroqLLM',
    'BigPickleLLM',
]
