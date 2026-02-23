"""Tests for worker indexing pipeline to improve coverage."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_job_status_values(self):
        """Test JobStatus enum values."""
        from apps.worker.indexing import JobStatus

        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.RETRYING.value == "retrying"


class TestJobState:
    """Tests for JobState."""

    def test_job_state_creation(self):
        """Test JobState creation."""
        from apps.worker.indexing import JobState, JobStatus

        state = JobState(job_id="test-123")
        assert state.job_id == "test-123"
        assert state.status == JobStatus.PENDING
        assert state.progress == 0.0

    def test_job_state_to_dict(self):
        """Test JobState to_dict."""
        from apps.worker.indexing import JobState, JobStatus

        state = JobState(job_id="test-123", status=JobStatus.RUNNING, progress=0.5)
        result = state.to_dict()

        assert result["job_id"] == "test-123"
        assert result["status"] == "running"
        assert result["progress"] == 0.5


class TestPipelineStage:
    """Tests for PipelineStage base class."""

    def test_pipeline_stage_creation(self):
        """Test PipelineStage creation."""
        from apps.worker.indexing import PipelineStage

        class TestStage(PipelineStage):
            def process(self, context):
                return context

        stage = TestStage("test")
        assert stage.name == "test"

    def test_pipeline_stage_not_implemented(self):
        """Test PipelineStage process raises NotImplementedError."""
        from apps.worker.indexing import PipelineStage

        stage = PipelineStage("test")
        with pytest.raises(NotImplementedError):
            stage.process(None)


class TestPipelineContext:
    """Tests for PipelineContext."""

    def test_pipeline_context_creation(self, temp_dir):
        """Test PipelineContext creation."""
        from apps.worker.indexing import PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )

        assert context.job_id == "test-job"
        assert context.input_path == "/input/test.pptx"
        assert context.slides == []
        assert context.embeddings == {}
        assert context.graph == {}

    def test_save_artifact_dict(self, temp_dir):
        """Test saving dict artifact."""
        from apps.worker.indexing import PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )

        data = {"key": "value"}
        context.save_artifact("test", data)

        artifact_path = Path(temp_dir) / "test-job_test.json"
        assert artifact_path.exists()

    def test_save_artifact_string(self, temp_dir):
        """Test saving string artifact."""
        from apps.worker.indexing import PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )

        context.save_artifact("text", "hello world")

        artifact_path = Path(temp_dir) / "test-job_text.json"
        assert artifact_path.exists()

    def test_load_artifact_exists(self, temp_dir):
        """Test loading existing artifact."""
        from apps.worker.indexing import PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )

        data = {"key": "value"}
        context.save_artifact("test", data)

        loaded = context.load_artifact("test")
        assert loaded == data

    def test_load_artifact_not_exists(self, temp_dir):
        """Test loading non-existing artifact."""
        from apps.worker.indexing import PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )

        loaded = context.load_artifact("nonexistent")
        assert loaded is None

    def test_compute_content_hash(self, temp_dir):
        """Test compute_content_hash."""
        from apps.worker.indexing import PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )

        context.slides = [{"title": "Test"}]
        hash1 = context.compute_content_hash()

        assert len(hash1) == 64  # SHA256 hex length


class TestRetryable:
    """Tests for Retryable decorator."""

    def test_retryable_success(self):
        """Test Retryable with successful function."""
        from apps.worker.indexing import Retryable

        @Retryable(max_attempts=3, backoff=0.1)
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

    def test_retryable_failure(self):
        """Test Retryable with failing function."""
        from apps.worker.indexing import Retryable

        @Retryable(max_attempts=2, backoff=0.1)
        def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            fail_func()


class TestPPTXParserStage:
    """Tests for PPTXParserStage."""

    def test_parser_with_cached_data(self, temp_dir):
        """Test parser with cached data."""
        from apps.worker.indexing import PipelineContext, PPTXParserStage

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )

        cached_slides = [{"slide_number": 1, "slide_id": "cached"}]
        context.save_artifact("parsed_slides", cached_slides)

        stage = PPTXParserStage()
        result = stage.process(context)

        assert result.slides == cached_slides


class TestOCRStage:
    """Tests for OCRStage."""

    def test_ocr_stage_creation(self):
        """Test OCRStage creation."""
        from apps.worker.indexing import OCRStage

        stage = OCRStage(ocr_provider="paddleocr", languages=["en"])
        assert stage.ocr_provider == "paddleocr"
        assert stage.languages == ["en"]

    def test_ocr_stage_unknown_provider(self, temp_dir):
        """Test OCRStage with unknown provider."""
        from apps.worker.indexing import OCRStage, PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )
        context.slides = [{"slide_number": 1, "images": []}]

        stage = OCRStage(ocr_provider="unknown")
        result = stage.process(context)

        assert result is not None


class TestStructureAnalyzerStage:
    """Tests for StructureAnalyzerStage."""

    def test_structure_analyzer(self, temp_dir):
        """Test structure analyzer."""
        from apps.worker.indexing import PipelineContext, StructureAnalyzerStage

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )
        context.slides = [
            {"slide_number": 1, "slide_id": "slide1", "title": "Introduction"},
            {"slide_number": 2, "slide_id": "slide2", "title": "Summary"},
        ]

        stage = StructureAnalyzerStage()
        result = stage.process(context)

        assert "sections" in result.metadata
        assert result.metadata["total_sections"] >= 1


class TestMetadataExtractionStage:
    """Tests for MetadataExtractionStage."""

    def test_metadata_extraction_creation(self):
        """Test MetadataExtractionStage creation."""
        from apps.worker.indexing import MetadataExtractionStage
        from unittest.mock import Mock

        mock_llm = Mock()
        stage = MetadataExtractionStage(llm_adapter=mock_llm)
        assert stage.name == "metadata"

    def test_metadata_extraction_with_cached(self, temp_dir):
        """Test metadata extraction with cached data."""
        from apps.worker.indexing import MetadataExtractionStage, PipelineContext
        from unittest.mock import Mock

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )
        context.slides = [{"slide_number": 1, "slide_id": "slide1"}]

        cached = {"slide1": {"keywords": ["test"]}}
        context.save_artifact("metadata", cached)

        mock_llm = Mock()
        stage = MetadataExtractionStage(llm_adapter=mock_llm)
        result = stage.process(context)

        assert result.slides[0].get("keywords") == ["test"]


class TestEmbeddingStage:
    """Tests for EmbeddingStage."""

    def test_embedding_stage_creation(self):
        """Test EmbeddingStage creation."""
        from apps.worker.indexing import EmbeddingStage

        stage = EmbeddingStage(embedder=None, batch_size=16)
        assert stage.name == "embedding"

    def test_embedding_with_cached(self, temp_dir):
        """Test embedding with cached data."""
        from apps.worker.indexing import EmbeddingStage, PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )
        context.slides = [
            {"slide_number": 1, "slide_id": "slide1", "title": "Test", "bullets": []}
        ]

        cached_embeddings = {"slide1": [0.1] * 384}
        context.save_artifact("embeddings", cached_embeddings)

        mock_embedder = Mock()
        stage = EmbeddingStage(embedder=mock_embedder)
        result = stage.process(context)

        assert result.embeddings == cached_embeddings


class TestGraphBuilderStage:
    """Tests for GraphBuilderStage."""

    def test_graph_builder(self, temp_dir):
        """Test graph builder."""
        from apps.worker.indexing import GraphBuilderStage, PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )
        context.slides = [
            {"slide_number": 1, "slide_id": "slide1", "title": "Test"},
        ]
        context.embeddings = {"slide1": [0.1] * 384}

        stage = GraphBuilderStage()
        result = stage.process(context)

        assert "nodes" in result.graph
        assert "edges" in result.graph


class TestIndexerWorker:
    """Tests for IndexerWorker."""

    @patch("apps.worker.indexing.create_llm_adapter")
    @patch("apps.worker.indexing.create_vector_store")
    @patch("apps.worker.indexing.get_config")
    def test_indexer_worker_creation(self, mock_config, mock_store, mock_llm):
        """Test IndexerWorker creation."""
        from apps.worker.indexing import IndexerWorker

        mock_llm.return_value = Mock()
        mock_store.return_value = Mock()
        mock_cfg = Mock()
        mock_cfg.worker.max_workers = 4
        mock_cfg.ocr.enabled = True
        mock_cfg.ocr.provider = "paddleocr"
        mock_cfg.ocr.languages = ["en"]
        mock_config.return_value = mock_cfg

        worker = IndexerWorker()
        assert len(worker.stages) > 0

    @patch("apps.worker.indexing.create_llm_adapter")
    @patch("apps.worker.indexing.create_vector_store")
    @patch("apps.worker.indexing.get_config")
    def test_indexer_stages_names(self, mock_config, mock_store, mock_llm):
        """Test stage names."""
        from apps.worker.indexing import IndexerWorker

        mock_llm.return_value = Mock()
        mock_store.return_value = Mock()
        mock_cfg = Mock()
        mock_cfg.worker.max_workers = 4
        mock_cfg.ocr.enabled = True
        mock_cfg.ocr.provider = "paddleocr"
        mock_cfg.ocr.languages = ["en"]
        mock_config.return_value = mock_cfg

        worker = IndexerWorker()
        stage_names = [s.name for s in worker.stages]
        assert "parser" in stage_names
        assert "structure" in stage_names
        assert "embedding" in stage_names
        assert "graph" in stage_names


class TestRunIndexing:
    """Tests for run_indexing function."""

    @patch("apps.worker.indexing.IndexerWorker")
    def test_run_indexing(self, mock_worker):
        """Test run_indexing convenience function."""
        from apps.worker.indexing import run_indexing

        mock_context = Mock()
        mock_context.job_id = "test-job"
        mock_context.slides = []
        mock_context.metadata = {"total_sections": 0}

        mock_worker_instance = Mock()
        mock_worker_instance.process.return_value = mock_context
        mock_worker.return_value = mock_worker_instance

        result = run_indexing("/input/test.pptx", "/output")

        assert result["job_id"] == "test-job"
        assert result["status"] == "completed"


class TestPipelineContextErrors:
    """Test PipelineContext error handling."""

    def test_context_with_errors_list(self, temp_dir):
        """Test context errors list."""
        from apps.worker.indexing import PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )

        context.errors.append("Error 1")
        context.errors.append("Error 2")

        assert len(context.errors) == 2


class TestMetadataExtractionBatch:
    """Test metadata extraction batch processing."""

    @patch("apps.worker.indexing.get_config")
    def test_metadata_with_llm_batch(self, mock_config, temp_dir):
        """Test metadata extraction with LLM batch."""
        from apps.worker.indexing import MetadataExtractionStage, PipelineContext

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.text = '{"keywords": ["test"], "learning_objectives": []}'
        mock_llm.batch_generate.return_value = [mock_response]

        mock_cfg = Mock()
        mock_cfg.llm.batch_size = 10
        mock_config.return_value = mock_cfg

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )
        context.slides = [
            {
                "slide_number": 1,
                "slide_id": "slide1",
                "title": "Test",
                "bullets": [{"text": "Point"}],
            }
        ]

        stage = MetadataExtractionStage(llm_adapter=mock_llm)
        result = stage.process(context)

        assert result.slides[0].get("keywords") == ["test"]

    @patch("apps.worker.indexing.get_config")
    def test_metadata_llm_exception(self, mock_config, temp_dir):
        """Test metadata extraction with LLM exception."""
        from apps.worker.indexing import MetadataExtractionStage, PipelineContext

        mock_llm = Mock()
        mock_llm.batch_generate.side_effect = Exception("LLM Error")

        mock_cfg = Mock()
        mock_cfg.llm.batch_size = 10
        mock_config.return_value = mock_cfg

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )
        context.slides = [
            {
                "slide_number": 1,
                "slide_id": "slide1",
                "title": "Test",
                "bullets": [{"text": "Point"}],
            }
        ]

        stage = MetadataExtractionStage(llm_adapter=mock_llm)
        result = stage.process(context)

        assert result is not None


class TestOCRStageWithPaddle:
    """Test OCR with paddleocr."""

    def test_ocr_with_paddle_provider(self, temp_dir):
        """Test OCR with paddle provider."""
        from apps.worker.indexing import OCRStage, PipelineContext

        context = PipelineContext(
            job_id="test-job",
            input_path="/input/test.pptx",
            output_dir=temp_dir,
            artifacts_dir=temp_dir,
        )
        context.slides = [
            {"slide_number": 1, "slide_id": "slide1", "title": "Test", "images": []}
        ]

        stage = OCRStage(ocr_provider="paddleocr", languages=["en"])
        result = stage.process(context)

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
