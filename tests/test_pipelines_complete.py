"""Tests for pipelines - simplified."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestPPTIndexer:
    """Tests for PPTIndexer."""

    def test_indexer_import(self):
        """Test PPTIndexer can be imported."""
        from pptx_indexer.pipelines.indexing_pipeline import PPTIndexer

        assert PPTIndexer is not None


class TestPPTRetriever:
    """Tests for PPTRetriever."""

    def test_retriever_import(self):
        """Test PPTRetriever can be imported."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever

        assert PPTRetriever is not None


class TestIndexingConfig:
    """Tests for IndexingConfig."""

    def test_indexing_config_defaults(self):
        """Test IndexingConfig defaults."""
        from pptx_indexer.config import IndexingConfig

        config = IndexingConfig()
        assert config.llm_model == "gpt-3.5-turbo"
        assert config.embedding_model == "all-MiniLM-L6-v2"


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_plugin_registry_import(self):
        """Test PluginRegistry can be imported."""
        from pptx_indexer.plugins.base_llm import PluginRegistry

        assert PluginRegistry is not None


class TestBaseClasses:
    """Tests for base classes."""

    def test_base_embedder(self):
        """Test BaseEmbedder is abstract."""
        from pptx_indexer.plugins.base_llm import BaseEmbedder
        import inspect

        assert inspect.isabstract(BaseEmbedder)

    def test_base_vector_store(self):
        """Test BaseVectorStore is abstract."""
        from pptx_indexer.plugins.base_llm import BaseVectorStore
        import inspect

        assert inspect.isabstract(BaseVectorStore)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
