"""Tests for PPTX Indexer - Basic test suite."""

import pytest

from pptx_indexer.core.slide_graph import SlideGraphBuilder
from pptx_indexer.core.structure_analyzer import StructureAnalyzer
from pptx_indexer.schemas.slide_node import BulletPoint, SlideNode


class TestSlideNode:
    """Test SlideNode functionality."""

    def test_slide_creation(self):
        """Test creating a slide node."""
        slide = SlideNode(
            slide_number=1,
            title="Introduction",
        )

        assert slide.slide_number == 1
        assert slide.title == "Introduction"
        assert len(slide.bullets) == 0

    def test_add_bullet(self):
        """Test adding bullets to slide."""
        slide = SlideNode(title="Test")

        bullet = BulletPoint(
            text="Main point",
            level=0,
            index=0,
        )
        slide.bullets.append(bullet)

        assert len(slide.bullets) == 1
        assert slide.bullets[0].text == "Main point"

    def test_get_full_text(self):
        """Test extracting full text from slide."""
        slide = SlideNode(
            title="Title",
            subtitle="Subtitle",
        )

        bullet = BulletPoint(text="Bullet", level=0, index=0)
        slide.bullets.append(bullet)

        full_text = slide.get_full_text()

        assert "Title" in full_text
        assert "Subtitle" in full_text
        assert "Bullet" in full_text


class TestStructureAnalyzer:
    """Test structure analysis."""

    def test_section_title_detection(self):
        """Test detecting section titles."""
        analyzer = StructureAnalyzer()

        # Create test slides
        slides = [
            SlideNode(slide_number=1, title="Main Topic", bullets=[]),
            SlideNode(
                slide_number=2,
                title="Section 1: Introduction",
                bullets=[],
            ),
        ]

        is_title = analyzer._is_section_title(slides[1])
        assert is_title

    def test_keyword_similarity(self):
        """Test keyword-based similarity."""
        analyzer = StructureAnalyzer()

        slide1 = SlideNode(slide_number=1, title="Machine Learning")
        slide1.keywords = ["ML", "AI", "algorithms"]

        slide2 = SlideNode(slide_number=2, title="Deep Learning")
        slide2.keywords = ["ML", "neural networks", "AI"]

        slides = [slide1, slide2]

        similarities = analyzer.compute_slide_similarity(slides)

        # Should have some similarity
        assert slide1.slide_id in similarities
        assert slide2.slide_id in similarities


class TestSlideGraph:
    """Test graph building."""

    def test_graph_node_creation(self):
        """Test creating graph nodes."""
        slide = SlideNode(slide_number=1, title="Test")

        builder = SlideGraphBuilder()
        node = builder._create_slide_node(slide)

        assert node.node_id == slide.slide_id
        assert node.node_type == "slide"
        assert node.content["title"] == "Test"

    def test_graph_building(self):
        """Test building complete graph."""
        from pptx_indexer.schemas.slide_node import SectionNode

        # Create test data
        slides = [
            SlideNode(slide_number=1, title="Slide 1"),
            SlideNode(slide_number=2, title="Slide 2"),
        ]

        section = SectionNode(title="Section 1")
        section.slide_ids = [s.slide_id for s in slides]

        builder = SlideGraphBuilder()
        graph = builder.build(slides, [section])

        # Verify graph structure
        assert len(graph.nodes) >= len(slides)
        assert len(graph.edges) > 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
