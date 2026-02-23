"""Tests for default plugin implementations to improve coverage."""

import pytest


class TestBigPickleLLM:
    """Test BigPickleLLM."""

    def test_bigpickellm_no_api_key(self):
        """Test BigPickleLLM without API key."""
        from pptx_indexer.plugins.default_plugins.implementations import BigPickleLLM

        llm = BigPickleLLM(api_key=None)
        assert llm.client is None

    def test_bigpickellm_api_key_none(self):
        """Test BigPickleLLM with api_key as None."""
        from pptx_indexer.plugins.default_plugins.implementations import BigPickleLLM

        llm = BigPickleLLM(api_key=None, base_url="https://custom.url")
        assert llm.base_url == "https://custom.url"

    def test_bigpickellm_generate_no_client(self):
        """Test BigPickleLLM generate without client."""
        from pptx_indexer.plugins.default_plugins.implementations import BigPickleLLM

        llm = BigPickleLLM(api_key=None)
        with pytest.raises(RuntimeError):
            llm.generate("test")

    def test_bigpickellm_batch_generate_no_client(self):
        """Test BigPickleLLM batch generate without client."""
        from pptx_indexer.plugins.default_plugins.implementations import BigPickleLLM

        llm = BigPickleLLM(api_key=None)
        with pytest.raises(RuntimeError):
            llm.batch_generate(["test"])


class TestOpenAILLM:
    """Test OpenAILLM."""

    def test_openai_initialization(self):
        """Test OpenAILLM initialization."""
        from pptx_indexer.plugins.default_plugins.implementations import OpenAILLM

        llm = OpenAILLM(api_key="test-key", model="gpt-4")
        assert llm.api_key == "test-key"
        assert llm.model == "gpt-4"

    def test_openai_initialization_with_kwargs(self):
        """Test OpenAILLM initialization with kwargs."""
        from pptx_indexer.plugins.default_plugins.implementations import OpenAILLM

        llm = OpenAILLM(api_key="test-key", model="gpt-4", temperature=0.5)
        assert llm.kwargs.get("temperature") == 0.5

    def test_openai_generate_error(self):
        """Test OpenAI generate error."""
        from pptx_indexer.plugins.default_plugins.implementations import OpenAILLM

        llm = OpenAILLM(api_key="test")
        with pytest.raises(Exception):
            llm.generate("test")

    def test_openai_batch_generate_error(self):
        """Test OpenAI batch generate error."""
        from pptx_indexer.plugins.default_plugins.implementations import OpenAILLM

        llm = OpenAILLM(api_key="test")
        with pytest.raises(Exception):
            llm.batch_generate(["test"])


class TestGeminiLLM:
    """Test GeminiLLM."""

    def test_gemini_initialization(self):
        """Test GeminiLLM initialization."""
        from pptx_indexer.plugins.default_plugins.implementations import GeminiLLM

        llm = GeminiLLM(api_key="test-key", model="gemini-pro")
        assert llm.api_key == "test-key"
        assert llm.model == "gemini-pro"

    def test_gemini_with_kwargs(self):
        """Test Gemini with kwargs."""
        from pptx_indexer.plugins.default_plugins.implementations import GeminiLLM

        llm = GeminiLLM(
            api_key="test",
            temperature=0.5,
            max_tokens=1024,
            top_p=0.9,
            top_k=50,
        )
        assert llm.kwargs.get("temperature") == 0.5

    def test_gemini_generate_error(self):
        """Test Gemini generate error."""
        from pptx_indexer.plugins.default_plugins.implementations import GeminiLLM

        llm = GeminiLLM(api_key="test")
        with pytest.raises(Exception):
            llm.generate("test")

    def test_gemini_batch_generate_error(self):
        """Test Gemini batch generate error."""
        from pptx_indexer.plugins.default_plugins.implementations import GeminiLLM

        llm = GeminiLLM(api_key="test")
        with pytest.raises(Exception):
            llm.batch_generate(["test"])


class TestChromaVectorStore:
    """Test ChromaVectorStore."""

    def test_chroma_initialization(self):
        """Test Chroma initialization."""
        from pptx_indexer.plugins.default_plugins.implementations import (
            ChromaVectorStore,
        )

        store = ChromaVectorStore(collection_name="test")
        assert store is not None

    def test_chroma_persist_dir(self):
        """Test Chroma persist directory."""
        from pptx_indexer.plugins.default_plugins.implementations import (
            ChromaVectorStore,
        )

        store = ChromaVectorStore(persist_dir="/tmp/chroma")
        assert store is not None

    def test_chroma_collection_name(self):
        """Test Chroma collection name."""
        from pptx_indexer.plugins.default_plugins.implementations import (
            ChromaVectorStore,
        )

        store = ChromaVectorStore(collection_name="my_collection")
        assert store is not None


class TestPluginExports:
    """Test plugin exports."""

    def test_all_exports(self):
        """Test all exports."""
        from pptx_indexer.plugins.default_plugins.implementations import __all__

        assert "OpenAILLM" in __all__
        assert "GeminiLLM" in __all__
        assert "BigPickleLLM" in __all__
        assert "SentenceTransformerEmbedder" in __all__
        assert "ChromaVectorStore" in __all__
        assert "PytesseractOCR" in __all__
        assert "PaddleOCR" in __all__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
