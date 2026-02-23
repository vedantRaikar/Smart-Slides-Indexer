"""Tests for vector store module - simplified."""

import pytest
from pathlib import Path


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test SearchResult creation."""
        from pptx_indexer.vector_store import SearchResult

        result = SearchResult(
            id="doc1", score=0.9, text="content", metadata={"key": "value"}
        )
        assert result.id == "doc1"
        assert result.score == 0.9


class TestEmbeddingCache:
    """Tests for EmbeddingCache."""

    def test_cache_initialization(self, temp_dir):
        """Test cache initialization."""
        from pptx_indexer.vector_store import EmbeddingCache

        cache = EmbeddingCache(cache_dir=temp_dir)
        assert cache.cache_dir == Path(temp_dir)

    def test_cache_key_generation(self, temp_dir):
        """Test cache key generation."""
        from pptx_indexer.vector_store import EmbeddingCache

        cache = EmbeddingCache(cache_dir=temp_dir)
        key1 = cache._get_cache_key("text", "model")
        key2 = cache._get_cache_key("text", "model")
        assert key1 == key2

    def test_cache_get_miss(self, temp_dir):
        """Test cache miss."""
        from pptx_indexer.vector_store import EmbeddingCache

        cache = EmbeddingCache(cache_dir=temp_dir)
        result = cache.get("nonexistent", "model")
        assert result is None


class TestBaseVectorStore:
    """Tests for BaseVectorStore."""

    def test_base_is_abstract(self):
        """Test BaseVectorStore is abstract."""
        from pptx_indexer.vector_store import BaseVectorStore
        import inspect

        assert inspect.isabstract(BaseVectorStore)


class TestVectorStoreFactory:
    """Tests for VectorStoreFactory."""

    def test_factory_exists(self):
        """Test VectorStoreFactory exists."""
        from pptx_indexer.vector_store import VectorStoreFactory

        assert VectorStoreFactory is not None


class TestCreateVectorStore:
    """Tests for create_vector_store factory."""

    def test_create_vector_store_function(self):
        """Test create_vector_store function."""
        from pptx_indexer.vector_store import create_vector_store

        assert callable(create_vector_store)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
