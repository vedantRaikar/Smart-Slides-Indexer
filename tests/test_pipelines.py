"""Tests for pipelines - minimal dependencies."""

import pytest


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

    def test_save_and_load_artifact(self):
        """Test artifact save and load."""
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

            test_data = {"key": "value", "list": [1, 2, 3]}
            context.save_artifact("test_data", test_data)

            loaded = context.load_artifact("test_data")
            assert loaded == test_data
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
