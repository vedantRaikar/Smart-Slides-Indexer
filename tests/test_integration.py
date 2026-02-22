"""Tests for CLI and integration - minimal dependencies."""

import pytest
from unittest.mock import Mock, patch


class TestCLI:
    """Tests for CLI commands."""

    def test_setup_logging(self):
        """Test logging setup."""
        from apps.cli.main import setup_logging

        setup_logging("INFO")


class TestMain:
    """Tests for main entry point."""

    def test_main_help(self):
        """Test main provides help."""
        from apps.cli.main import main
        import sys

        with patch.object(sys, "argv", ["main", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestCLICommands:
    """Tests for CLI command functions."""

    def test_cmd_info(self):
        """Test info command."""
        from apps.cli.main import cmd_info

        mock_config = Mock()
        mock_config.app_name = "test-app"
        mock_config.environment = "test"
        mock_config.llm.provider = "groq"
        mock_config.llm.model = "test-model"
        mock_config.llm.cache_enabled = True
        mock_config.embedder.model = "test-embedder"
        mock_config.embedder.device = "cpu"
        mock_config.vector_store.provider = "chroma"
        mock_config.vector_store.collection_name = "test-collection"
        mock_config.ocr.provider = "paddleocr"
        mock_config.ocr.enabled = True

        with patch("apps.cli.main.get_config", return_value=mock_config):
            with patch("builtins.print"):
                cmd_info(Mock())

    def test_cmd_index_file_not_found(self):
        """Test index command with missing file."""
        from apps.cli.main import cmd_index
        import sys

        args = Mock()
        args.input = "/nonexistent/file.pptx"
        args.output = "./output"
        args.job_id = None
        args.log_level = "INFO"

        with pytest.raises(SystemExit) as exc_info:
            cmd_index(args)
        assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
