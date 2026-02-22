"""Tests for core utilities - minimal dependencies."""

from unittest.mock import Mock, patch

import pytest


class TestConfig:
    """Tests for configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        from pptx_indexer.config import get_config

        config = get_config()

    def test_retry_success(self):
        """Test retry on successful call."""
        from apps.worker.indexing import Retryable

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        import os

        from pptx_indexer.config import AppConfig

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


class TestPipelineContext:
    """Tests for Pipeline context."""

    def test_context_creation(self):
        """Test context creation."""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        try:
            from apps.worker.indexing import PipelineContext

            context = PipelineContext(
                job_id="test-123",
                input_path="/test/input.pptx",
                output_dir=temp_dir,
                artifacts_dir=temp_dir,
            )

            assert context.job_id == "test-123"
            assert context.input_path == "/test/input.pptx"
            assert len(context.slides) == 0
            assert len(context.embeddings) == 0
            assert len(context.stages_completed) == 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cache_operations(self):
        """Test LLM cache."""
        import shutil
        import tempfile

        from pptx_indexer.llm_adapter import LLMCache

        temp_dir = tempfile.mkdtemp()
        try:
            from apps.worker.indexing import PipelineContext

            context = PipelineContext(
                job_id="test-123",
                input_path="/test/input.pptx",
                output_dir=temp_dir,
                artifacts_dir=temp_dir,
            )

            test_data = {"key": "value", "list": [1, 2, 3]}
            context.save_artifact("test_data", test_data)

            loaded = context.load_artifact("test_data")
            assert loaded == test_data
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestMetadataExtractionStage:
    """Tests for metadata extraction stage."""

    def test_stage_initialization_with_mock(self):
        """Test metadata extraction stage initialization with mock."""
        from unittest.mock import Mock, patch

        mock_llm = Mock()

        with patch("apps.worker.indexing.create_llm_adapter", return_value=mock_llm):
            from apps.worker.indexing import MetadataExtractionStage

            stage = MetadataExtractionStage()
            assert stage.name == "metadata"


class TestJobState:
    """Tests for JobState class."""

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

        try:
            context = PipelineContext(
                job_id="test-123",
                input_path="/test/input.pptx",
                output_dir=temp_dir,
                artifacts_dir=temp_dir,
            )
            context.slides = [
                {"slide_id": "s1", "slide_number": 1, "title": "Introduction"},
                {"slide_id": "s2", "slide_number": 2, "title": "Summary"},
            ]

            stage = StructureAnalyzerStage()
            result = stage.process(context)

            assert "sections" in result.metadata
            assert result.metadata["total_sections"] > 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestOCRStage:
    """Tests for OCRStage."""

    def test_ocr_stage_initialization(self):
        """Test OCR stage initialization."""
        from apps.worker.indexing import OCRStage

        stage = OCRStage(ocr_provider="paddleocr", languages=["en"])
        assert stage.name == "ocr"
        assert stage.ocr_provider == "paddleocr"
        assert stage.languages == ["en"]

    def test_ocr_stage_default_languages(self):
        """Test OCR stage default languages."""
        from apps.worker.indexing import OCRStage

        stage = OCRStage()
        assert stage.languages == ["en"]


class TestGraphBuilderStage:
    """Tests for GraphBuilderStage."""

    def test_graph_builder_with_embeddings(self, temp_dir):
        """Test graph builder with embeddings."""
        import shutil
        from apps.worker.indexing import PipelineContext, GraphBuilderStage

        try:
            context = PipelineContext(
                job_id="test-123",
                input_path="/test/input.pptx",
                output_dir=temp_dir,
                artifacts_dir=temp_dir,
            )
            context.slides = [
                {"slide_id": "s1", "slide_number": 1, "title": "Intro"},
                {"slide_id": "s2", "slide_number": 2, "title": "Content"},
            ]
            context.embeddings = {
                "s1": [0.1] * 384,
                "s2": [0.2] * 384,
            }

            stage = GraphBuilderStage()
            result = stage.process(context)

            assert "nodes" in result.graph
            assert "edges" in result.graph
            assert result.graph["stats"]["total_nodes"] == 2
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestEmbeddingStage:
    """Tests for EmbeddingStage."""

    def test_embedding_stage_initialization(self):
        """Test embedding stage initialization."""
        from apps.worker.indexing import EmbeddingStage

        stage = EmbeddingStage(batch_size=16, cache_enabled=False)
        assert stage.name == "embedding"
        assert stage.batch_size == 16
        assert stage.cache_enabled is False


class TestPPTXParserStage:
    """Tests for PPTXParserStage."""

    def test_parser_stage_initialization(self):
        """Test parser stage initialization."""
        from apps.worker.indexing import PPTXParserStage

        stage = PPTXParserStage()
        assert stage.name == "parser"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
