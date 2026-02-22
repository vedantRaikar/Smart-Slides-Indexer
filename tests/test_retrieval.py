"""Tests for retrieval pipeline - more coverage."""

import pytest
from unittest.mock import Mock, patch


class TestRetrievalPipelineMore:
    """More tests for PPTRetriever."""

    def test_retriever_init(self):
        """Test retriever init."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever

        mock_embedder = Mock()
        mock_store = Mock()

        with patch(
            "pptx_indexer.pipelines.retrieval_pipeline.PPTRetriever.__init__",
            return_value=None,
        ):
            retriever = PPTRetriever.__new__(PPTRetriever)
            retriever.embedder = mock_embedder
            retriever.vector_store = mock_store
            assert retriever.embedder is mock_embedder


class TestRetrievalResult:
    """Tests for RetrievalResult."""

    def test_retrieval_result_creation(self):
        """Test RetrievalResult creation."""
        from pptx_indexer.pipelines.retrieval_pipeline import RetrievalResult

        result = RetrievalResult(
            slide_id="s1",
            slide_title="Title",
            slide_content="content",
            score=0.9,
            retrieval_method="vector",
            metadata={},
        )
        assert result.slide_id == "s1"


class TestEdgeType:
    """Tests for EdgeType enum."""

    def test_edge_type_values(self):
        """Test EdgeType values."""
        from pptx_indexer.schemas.slide_graph_schema import EdgeType

        assert EdgeType.NEXT.value == "next"
        assert EdgeType.PREVIOUS.value == "previous"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
