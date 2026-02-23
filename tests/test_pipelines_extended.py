"""Tests for pipeline modules."""

import pytest
from unittest.mock import Mock, patch


class TestIndexingPipeline:
    """Tests for IndexingPipeline."""

    def test_import_indexing_pipeline(self):
        """Test importing indexing pipeline."""
        from pptx_indexer.pipelines.indexing_pipeline import PPTIndexer

        assert PPTIndexer is not None


class TestRetrievalPipeline:
    """Tests for RetrievalPipeline."""

    def test_import_retrieval_pipeline(self):
        """Test importing retrieval pipeline."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever

        assert PPTRetriever is not None


class TestConfig:
    """Tests for configuration."""

    def test_get_config(self):
        """Test getting config."""
        from pptx_indexer.config import get_config

        config = get_config()
        assert config is not None


class TestLLMAdapter:
    """Tests for LLM adapter."""

    def test_llm_adapter_import(self):
        """Test LLM adapter import."""
        from pptx_indexer.llm_adapter import LLMAdapter

        assert LLMAdapter is not None


class TestVectorStore:
    """Tests for vector store."""

    def test_create_vector_store(self):
        """Test vector store creation."""
        from pptx_indexer.vector_store import create_vector_store

        with patch("pptx_indexer.vector_store.ChromaVectorStore") as mock_chroma:
            mock_store = Mock()
            mock_chroma.return_value = mock_store

            store = create_vector_store()
            assert store is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
