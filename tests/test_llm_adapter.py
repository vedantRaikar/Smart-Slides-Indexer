"""Tests for LLM adapter module - simplified."""

import pytest
from pathlib import Path


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_llm_response_creation(self):
        """Test LLMResponse creation."""
        from pptx_indexer.llm_adapter import LLMResponse

        response = LLMResponse(text="test response", model="gpt-3.5")
        assert response.text == "test response"
        assert response.model == "gpt-3.5"
        assert response.cached is False


class TestLLMCache:
    """Tests for LLMCache."""

    def test_cache_initialization(self, temp_dir):
        """Test cache initialization."""
        from pptx_indexer.llm_adapter import LLMCache

        cache = LLMCache(cache_dir=temp_dir)
        assert cache.cache_dir == Path(temp_dir)

    def test_cache_key_generation(self, temp_dir):
        """Test cache key generation."""
        from pptx_indexer.llm_adapter import LLMCache

        cache = LLMCache(cache_dir=temp_dir)
        key1 = cache._get_cache_key("prompt", "model")
        key2 = cache._get_cache_key("prompt", "model")
        assert key1 == key2

    def test_cache_get_miss(self, temp_dir):
        """Test cache miss."""
        from pptx_indexer.llm_adapter import LLMCache

        cache = LLMCache(cache_dir=temp_dir)
        result = cache.get("nonexistent prompt", "model")
        assert result is None

    def test_cache_set_and_get(self, temp_dir):
        """Test cache set and get."""
        from pptx_indexer.llm_adapter import LLMCache, LLMResponse

        cache = LLMCache(cache_dir=temp_dir)
        response = LLMResponse(text="test response", model="gpt-3.5", tokens_used=50)
        cache.set(response, "test prompt")

        result = cache.get("test prompt", "gpt-3.5")
        assert result is not None
        assert result.text == "test response"
        assert result.cached is True


class TestBaseLLMAdapter:
    """Tests for BaseLLMAdapter."""

    def test_base_adapter_is_abstract(self):
        """Test BaseLLMAdapter is abstract."""
        from pptx_indexer.llm_adapter import BaseLLMAdapter
        import inspect

        assert inspect.isabstract(BaseLLMAdapter)


class TestLLMAdapterBasics:
    """Tests for LLMAdapter basics."""

    def test_llm_adapter_adapters_dict(self):
        """Test ADAPTERS dictionary exists."""
        from pptx_indexer.llm_adapter import LLMAdapter

        assert "openai" in LLMAdapter.ADAPTERS
        assert "groq" in LLMAdapter.ADAPTERS
        assert "gemini" in LLMAdapter.ADAPTERS

    def test_create_llm_adapter_function(self):
        """Test create_llm_adapter function."""
        from pptx_indexer.llm_adapter import create_llm_adapter

        assert callable(create_llm_adapter)


class TestBigPickleAdapter:
    """Tests for BigPickleAdapter."""

    def test_bigpickle_no_api_key(self):
        """Test BigPickle without API key."""
        from pptx_indexer.llm_adapter import BigPickleAdapter

        adapter = BigPickleAdapter(api_key=None)
        assert adapter._client is None

    def test_bigpickle_generate_no_client(self):
        """Test BigPickle generate without client."""
        from pptx_indexer.llm_adapter import BigPickleAdapter

        adapter = BigPickleAdapter(api_key=None)
        with pytest.raises(RuntimeError):
            adapter.generate("test prompt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
