"""PPTX Indexer - Complete framework initialization."""

from .pipelines.indexing_pipeline import PPTIndexer
from .pipelines.retrieval_pipeline import PPTRetriever
from .plugins.default_plugins import (
    ChromaVectorStore,
    GeminiLLM,
    OpenAILLM,
    PytesseractOCR,
    SentenceTransformerEmbedder,
)
from .schemas import (
    DocumentIndex,
    SectionNode,
    SlideGraph,
    SlideNode,
)

__version__ = "1.0.0"
__all__ = [
    "PPTIndexer",
    "PPTRetriever",
    "OpenAILLM",
    "GeminiLLM",
    "SentenceTransformerEmbedder",
    "ChromaVectorStore",
    "PytesseractOCR",
    "SlideNode",
    "SectionNode",
    "DocumentIndex",
    "SlideGraph",
]
