"""Tests for core modules - more comprehensive."""

import pytest
from unittest.mock import Mock, patch
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestParserMore:
    """More tests for PPTParser."""

    @patch("pptx_indexer.core.parser.Presentation")
    def test_parse_empty_presentation(self, mock_pres):
        """Test parsing empty presentation."""
        from pptx_indexer.core.parser import PPTParser

        mock_pres_instance = Mock()
        mock_pres_instance.slides = []
        mock_pres.return_value = mock_pres_instance

        parser = PPTParser()
        slides = parser.parse("/test.pptx")
        assert slides == []

    def test_parse_slide_metadata(self):
        """Test parse_slide_metadata."""
        from pptx_indexer.core.parser import PPTParser

        mock_slide = Mock()
        mock_slide.slide_layout = Mock()
        mock_slide.slide_layout.name = "Title"
        mock_slide.has_notes_slide = False
        mock_slide.shapes = []

        parser = PPTParser()
        metadata = parser.parse_slide_metadata(mock_slide)
        assert metadata["layout_name"] == "Title"


class TestSlideGraphMore:
    """More tests for SlideGraphBuilder."""

    def test_builder_with_similarity_threshold(self):
        """Test builder with custom similarity threshold."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder

        builder = SlideGraphBuilder(similarity_threshold=0.8)
        assert builder.similarity_threshold == 0.8


class TestStructureAnalyzerMore:
    """More tests for StructureAnalyzer."""

    def test_analyzer_with_threshold(self):
        """Test analyzer with custom threshold."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer

        analyzer = StructureAnalyzer(similarity_threshold=0.5)
        assert analyzer.similarity_threshold == 0.5


class TestMetadataExtractorMore:
    """More tests for MetadataExtractor."""

    def test_extractor_init(self):
        """Test extractor init."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor

        mock_llm = Mock()
        mock_llm.generate.return_value = "test"
        extractor = MetadataExtractor(llm=mock_llm)
        assert extractor.llm is mock_llm


class TestIndexBuilderMore:
    """More tests for IndexBuilder."""

    def test_builder_init(self):
        """Test builder init."""
        from pptx_indexer.core.index_builder import IndexBuilder

        mock_embedder = Mock()
        mock_embedder.embed.return_value = [[0.1]]
        builder = IndexBuilder(embedder=mock_embedder)
        assert builder.embedder is mock_embedder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
