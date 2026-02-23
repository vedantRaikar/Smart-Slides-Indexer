"""Tests for schema modules - simplified."""

import pytest
from unittest.mock import Mock, patch


class TestSlideNode:
    """Tests for SlideNode."""

    def test_slide_node_creation(self):
        """Test SlideNode creation."""
        from pptx_indexer.schemas.slide_node import SlideNode
        from pptx_indexer.schemas.slide_node import SlideNode, ContentType

        node = SlideNode(
            slide_number=1,
            title="Test Slide",
        )
        assert node.slide_number == 1
        assert node.title == "Test Slide"

    def test_slide_node_defaults(self):
        """Test SlideNode defaults."""
        from pptx_indexer.schemas.slide_node import SlideNode

        node = SlideNode(slide_number=1)
        assert node.bullets == []
        assert node.images == []


class TestSectionNode:
    """Tests for SectionNode."""

    def test_section_node_creation(self):
        """Test SectionNode creation."""
        from pptx_indexer.schemas.slide_node import SectionNode

        node = SectionNode(
            title="Introduction",
            slide_ids=["s1", "s2"],
        )
        assert node.title == "Introduction"
        assert len(node.slide_ids) == 2


class TestTableNode:
    """Tests for TableNode."""

    def test_table_node_creation(self):
        """Test TableNode creation."""
        from pptx_indexer.schemas.slide_node import TableNode

        node = TableNode(
            table_id="t1",
            headers=["Col1", "Col2"],
            rows=[["a", "b"]],
        )
        assert node.table_id == "t1"
        assert len(node.headers) == 2


class TestSlideGraphSchema:
    """Tests for SlideGraph schema."""

    def test_slide_graph_creation(self):
        """Test SlideGraph creation."""
        from pptx_indexer.schemas.slide_graph_schema import SlideGraph

        graph = SlideGraph()
        assert graph is not None
        assert graph.nodes == {}
        assert graph.edges == []

    def test_slide_graph_node_creation(self):
        """Test SlideGraphNode creation."""
        from pptx_indexer.schemas.slide_graph_schema import SlideGraphNode

        node = SlideGraphNode(
            node_id="n1",
            node_type="slide",
            content={"title": "Test"},
        )
        assert node.node_id == "n1"
        assert node.node_type == "slide"

    def test_graph_edge_creation(self):
        """Test GraphEdge creation."""
        from pptx_indexer.schemas.slide_graph_schema import GraphEdge, EdgeType

        edge = GraphEdge(
            source_id="s1",
            target_id="s2",
            edge_type=EdgeType.NEXT,
            weight=1.0,
        )
        assert edge.source_id == "s1"
        assert edge.edge_type == EdgeType.NEXT


class TestDocumentIndex:
    """Tests for DocumentIndex."""

    def test_document_index_creation(self):
        """Test DocumentIndex creation."""
        from pptx_indexer.schemas.document_index import DocumentIndex

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test Document",
            document_path="/test.pptx",
        )
        assert index.document_id == "doc1"


class TestContentType:
    """Tests for ContentType enum."""

    def test_content_type_values(self):
        """Test ContentType enum values."""
        from pptx_indexer.schemas.slide_node import ContentType

        assert ContentType.TITLE.value == "title"
        assert ContentType.TEXT.value == "text"


class TestNodeType:
    """Tests for NodeType enum."""

    def test_node_type_values(self):
        """Test NodeType enum values."""
        from pptx_indexer.schemas.slide_node import NodeType

        assert NodeType.SLIDE.value == "slide"
        assert NodeType.SECTION.value == "section"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
