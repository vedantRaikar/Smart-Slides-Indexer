"""Core module initialization."""
from .parser import PPTParser
from .structure_analyzer import StructureAnalyzer
from .slide_graph import SlideGraphBuilder
from .metadata_extractor import MetadataExtractor
from .index_builder import IndexBuilder

__all__ = [
    "PPTParser",
    "StructureAnalyzer",
    "SlideGraphBuilder",
    "MetadataExtractor",
    "IndexBuilder",
]
