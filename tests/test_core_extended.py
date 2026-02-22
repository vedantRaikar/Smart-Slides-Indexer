"""Tests for core modules - simplified."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestParserExtended:
    """Extended tests for PPTParser."""

    def test_parser_initialization(self, temp_dir):
        """Test parser initialization."""
        from pptx_indexer.core.parser import PPTParser

        parser = PPTParser(output_dir=temp_dir)
        assert parser.output_dir == temp_dir


class TestSlideGraphBuilderExtended:
    """Extended tests for SlideGraphBuilder."""

    def test_builder_creation(self):
        """Test builder creation."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder

        builder = SlideGraphBuilder()
        assert builder is not None


class TestStructureAnalyzerExtended:
    """Extended tests for StructureAnalyzer."""

    def test_analyzer_creation(self):
        """Test analyzer creation."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer

        analyzer = StructureAnalyzer()
        assert analyzer is not None


class TestMetadataExtractorExtended:
    """Extended tests for MetadataExtractor."""

    def test_extractor_init_with_mock(self):
        """Test extractor initialization with mock LLM."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor

        mock_llm = Mock()
        extractor = MetadataExtractor(llm=mock_llm)
        assert extractor.llm is mock_llm


class TestIndexBuilderExtended:
    """Extended tests for IndexBuilder."""

    def test_builder_init_with_mock(self):
        """Test builder initialization with mock embedder."""
        from pptx_indexer.core.index_builder import IndexBuilder

        mock_embedder = Mock()
        builder = IndexBuilder(embedder=mock_embedder)
        assert builder.embedder is mock_embedder


class TestCoreUtils:
    """Tests for core utilities."""

    def test_utils_module_imports(self):
        """Test utils can be imported."""
        from pptx_indexer.core import utils

        assert utils is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
