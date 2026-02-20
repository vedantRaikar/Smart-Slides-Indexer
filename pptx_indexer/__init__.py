"""
PPTX Indexer - Complete framework initialization.
"""

from .pipelines.indexing_pipeline import PPTIndexer
from .pipelines.retrieval_pipeline import PPTRetriever
from .plugins.default_plugins import (
    OpenAILLM,
    SentenceTransformerEmbedder,
    ChromaVectorStore,
    PytesseractOCR,
)
from .schemas import (
    SlideNode,
    SectionNode,
    DocumentIndex,
    SlideGraph,
)

__version__ = "1.0.0"
__all__ = [
    "PPTIndexer",
    "PPTRetriever",
    "OpenAILLM",
    "SentenceTransformerEmbedder",
    "ChromaVectorStore",
    "PytesseractOCR",
    "SlideNode",
    "SectionNode",
    "DocumentIndex",
    "SlideGraph",
]
