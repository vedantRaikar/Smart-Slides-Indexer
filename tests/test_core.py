"""Unit tests for core modules."""

from unittest.mock import Mock, patch

import pytest


class TestConfig:
    """Tests for configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        from pptx_indexer.config import get_config

        config = get_config()

        assert config.app_name == "smart-slides-indexer"
        assert config.environment == "development"
        assert config.llm.provider == "groq"
        assert config.embedder.model == "all-MiniLM-L6-v2"

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        import os

        from pptx_indexer.config import AppConfig

        os.environ["LLM__PROVIDER"] = "openai"
        os.environ["LLM__MODEL"] = "gpt-4"

        config = AppConfig()

        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4"

        # Cleanup
        del os.environ["LLM__PROVIDER"]
        del os.environ["LLM__MODEL"]


class TestLLMAdapter:
    """Tests for LLM adapter."""

    @patch("pptx_indexer.llm_adapter.GroqAdapter")
    def test_create_adapter(self, mock_adapter):
        """Test adapter creation."""
        from pptx_indexer.llm_adapter import LLMAdapter

        mock_adapter_instance = Mock()
        mock_adapter_instance.model = "llama-3.1-70b-versatile"
        mock_adapter.return_value = mock_adapter_instance

        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
            adapter = LLMAdapter(provider="groq", model="test-model")

        mock_adapter.assert_called_once()

    def test_cache_operations(self):
        """Test LLM cache."""
        import shutil
        import tempfile

        from pptx_indexer.llm_adapter import LLMCache

        cache_dir = tempfile.mkdtemp()
        try:
            cache = LLMCache(cache_dir)

            # Test cache miss
            result = cache.get("test prompt", "test-model")
            assert result is None

            # Test cache set and get
            from pptx_indexer.llm_adapter import LLMResponse

            response = LLMResponse(text="test response", model="test-model")
            cache.set(response, "test prompt")

            cached = cache.get("test prompt", "test-model")
            assert cached is not None
            assert cached.text == "test response"
            assert cached.cached is True
        finally:
            shutil.rmtree(cache_dir)


class TestVectorStore:
    """Tests for vector store."""

    @patch("chromadb.PersistentClient")
    def test_chroma_creation(self, mock_chroma):
        """Test Chroma vector store creation."""
        from pptx_indexer.vector_store import ChromaVectorStore

        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock_chroma.return_value.get_or_create_collection.return_value = mock_collection

        store = ChromaVectorStore(
            collection_name="test",
            persist_directory="/tmp/test",
        )

        assert store.collection_name == "test"
        mock_chroma.assert_called_once()


class TestPipelineContext:
    """Tests for pipeline context."""

    def test_context_creation(self):
        """Test pipeline context initialization."""
        from apps.worker.indexing import PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/test/input.pptx",
            output_dir="/test/output",
            artifacts_dir="/test/artifacts",
        )

        assert context.job_id == "test-job"
        assert len(context.slides) == 0
        assert len(context.embeddings) == 0

    def test_artifact_save_load(self):
        """Test artifact persistence."""
        import shutil
        import tempfile

        from apps.worker.indexing import PipelineContext

        temp_dir = tempfile.mkdtemp()
        try:
            context = PipelineContext(
                job_id="test-job",
                input_path="/test/input.pptx",
                output_dir=temp_dir,
                artifacts_dir=temp_dir,
            )

            # Save artifact
            test_data = {"key": "value"}
            context.save_artifact("test_artifact", test_data)

            # Load artifact
            loaded = context.load_artifact("test_artifact")
            assert loaded == test_data
        finally:
            shutil.rmtree(temp_dir)


class TestRetryable:
    """Tests for retry decorator."""

    def test_retry_success(self):
        """Test retry on successful call."""
        from apps.worker.indexing import Retryable

        @Retryable(max_attempts=3, backoff=0.1)
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

    def test_retry_failure(self):
        """Test retry on failure."""
        from apps.worker.indexing import Retryable

        @Retryable(max_attempts=3, backoff=0.1)
        def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            fail_func()


class TestMetadataExtraction:
    """Tests for metadata extraction stage."""

    def test_stage_initialization(self):
        """Test metadata extraction stage initialization."""
        from apps.worker.indexing import MetadataExtractionStage

        stage = MetadataExtractionStage()
        assert stage.name == "metadata"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
