"""Tests for plugins - more comprehensive."""

import pytest
from unittest.mock import Mock, patch


class TestPluginRegistryMore:
    """More tests for PluginRegistry."""

    def test_registry_init(self):
        """Test registry init."""
        from pptx_indexer.plugins.base_llm import PluginRegistry

        mock_llm = Mock()
        mock_embedder = Mock()
        mock_store = Mock()

        registry = PluginRegistry(
            llm=mock_llm,
            embedder=mock_embedder,
            vector_store=mock_store,
        )
        assert registry.llm is mock_llm
        assert registry.embedder is mock_embedder
        assert registry.vector_store is mock_store

    def test_registry_validate(self):
        """Test registry validate."""
        from pptx_indexer.plugins.base_llm import PluginRegistry

        mock_llm = Mock()
        mock_embedder = Mock()
        mock_store = Mock()

        registry = PluginRegistry(
            llm=mock_llm, embedder=mock_embedder, vector_store=mock_store
        )
        assert registry.validate() is True


class TestBaseLLMMore:
    """More tests for BaseLLM."""

    def test_base_llm_methods(self):
        """Test BaseLLM has required methods."""
        from pptx_indexer.plugins.base_llm import BaseLLM

        assert hasattr(BaseLLM, "generate")
        assert hasattr(BaseLLM, "batch_generate")


class TestBaseEmbedderMore:
    """More tests for BaseEmbedder."""

    def test_base_embedder_methods(self):
        """Test BaseEmbedder has required methods."""
        from pptx_indexer.plugins.base_llm import BaseEmbedder

        assert hasattr(BaseEmbedder, "embed")


class TestBaseOCRMore:
    """More tests for BaseOCR."""

    def test_base_ocr_methods(self):
        """Test BaseOCR has required methods."""
        from pptx_indexer.plugins.base_llm import BaseOCR

        assert hasattr(BaseOCR, "extract_text")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
