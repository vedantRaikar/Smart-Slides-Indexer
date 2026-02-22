"""Tests for core modules."""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestParser:
    """Tests for PPTParser."""

    def test_parser_initialization(self, temp_dir):
        """Test parser initialization."""
        from pptx_indexer.core.parser import PPTParser

        parser = PPTParser(output_dir=temp_dir)
        assert parser.output_dir == temp_dir

    def test_parse_slide_metadata(self):
        """Test slide metadata extraction."""
        from pptx_indexer.core.parser import PPTParser

        mock_slide = Mock()
        mock_slide.slide_layout = Mock()
        mock_slide.slide_layout.name = "Title Slide"
        mock_slide.has_notes_slide = True
        mock_slide.shapes = []

        parser = PPTParser()
        metadata = parser.parse_slide_metadata(mock_slide)

        assert metadata["layout_name"] == "Title Slide"
        assert metadata["has_notes"] is True
        assert metadata["shape_count"] == 0

    @patch("pptx_indexer.core.parser.Presentation")
    def test_get_presentation_info(self, mock_pres):
        """Test presentation info extraction."""
        from pptx_indexer.core.parser import PPTParser

        mock_pres_instance = Mock()
        mock_pres_instance.slides = []
        mock_pres_instance.slide_width = Mock(inches=10)
        mock_pres_instance.slide_height = Mock(inches=7.5)
        mock_pres_instance.slide_master = Mock()
        mock_pres.return_value = mock_pres_instance

        parser = PPTParser()
        info = parser.get_presentation_info("/test.pptx")

        assert "slide_count" in info
        assert "dimensions" in info


class TestSlideGraph:
    """Tests for SlideGraphBuilder."""

    def test_graph_builder_creation(self):
        """Test slide graph builder creation."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder

        builder = SlideGraphBuilder()
        assert builder.similarity_threshold == 0.6

    def test_graph_builder_custom_threshold(self):
        """Test slide graph builder with custom threshold."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder

        builder = SlideGraphBuilder(similarity_threshold=0.5)
        assert builder.similarity_threshold == 0.5


class TestStructureAnalyzer:
    """Tests for StructureAnalyzer."""

    def test_analyzer_creation(self):
        """Test analyzer creation."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer

        analyzer = StructureAnalyzer()
        assert analyzer.similarity_threshold == 0.6

    def test_analyzer_custom_threshold(self):
        """Test analyzer with custom threshold."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer

        analyzer = StructureAnalyzer(similarity_threshold=0.7)
        assert analyzer.similarity_threshold == 0.7


class TestMetadataExtractor:
    """Tests for MetadataExtractor."""

    def test_extractor_requires_llm(self):
        """Test that extractor requires LLM."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor

        mock_llm = Mock()
        extractor = MetadataExtractor(llm=mock_llm)
        assert extractor.llm is not None


class TestIndexBuilder:
    """Tests for IndexBuilder."""

    def test_builder_requires_embedder(self):
        """Test that builder requires embedder."""
        from pptx_indexer.core.index_builder import IndexBuilder

        mock_embedder = Mock()
        builder = IndexBuilder(embedder=mock_embedder)
        assert builder.embedder is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
