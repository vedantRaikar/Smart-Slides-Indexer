"""Tests for core utils."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch


class TestUtils:
    """Tests for utils functions."""

    def test_setup_logging_default(self):
        """Test setup_logging with defaults."""
        from pptx_indexer.core.utils import setup_logging

        setup_logging()

    def test_setup_logging_with_level(self):
        """Test setup_logging with level."""
        from pptx_indexer.core.utils import setup_logging

        setup_logging("DEBUG")

    def test_setup_logging_with_file(self, temp_dir):
        """Test setup_logging with file."""
        from pptx_indexer.core.utils import setup_logging

        log_file = os.path.join(temp_dir, "test.log")
        setup_logging("INFO", log_file)
        assert os.path.exists(log_file)

    def test_ensure_directory(self, temp_dir):
        """Test ensure_directory."""
        from pptx_indexer.core.utils import ensure_directory

        new_dir = os.path.join(temp_dir, "subdir", "nested")
        result = ensure_directory(new_dir)
        assert os.path.exists(new_dir)

    def test_validate_pptx_file_valid(self, temp_dir):
        """Test validate_pptx_file with valid file."""
        from pptx_indexer.core.utils import validate_pptx_file

        test_file = os.path.join(temp_dir, "test.pptx")
        Path(test_file).touch()
        assert validate_pptx_file(test_file) is True

    def test_validate_pptx_file_not_found(self):
        """Test validate_pptx_file with missing file."""
        from pptx_indexer.core.utils import validate_pptx_file

        with pytest.raises(FileNotFoundError):
            validate_pptx_file("/nonexistent/file.pptx")

    def test_validate_pptx_file_wrong_extension(self, temp_dir):
        """Test validate_pptx_file with wrong extension."""
        from pptx_indexer.core.utils import validate_pptx_file

        test_file = os.path.join(temp_dir, "test.pdf")
        Path(test_file).touch()
        with pytest.raises(ValueError):
            validate_pptx_file(test_file)

    def test_format_bytes_b(self):
        """Test format_bytes with bytes."""
        from pptx_indexer.core.utils import format_bytes

        assert format_bytes(100) == "100.00 B"

    def test_format_bytes_kb(self):
        """Test format_bytes with KB."""
        from pptx_indexer.core.utils import format_bytes

        assert format_bytes(1024) == "1.00 KB"

    def test_format_bytes_mb(self):
        """Test format_bytes with MB."""
        from pptx_indexer.core.utils import format_bytes

        assert format_bytes(1048576) == "1.00 MB"

    def test_format_bytes_gb(self):
        """Test format_bytes with GB."""
        from pptx_indexer.core.utils import format_bytes

        assert format_bytes(1073741824) == "1.00 GB"

    def test_format_bytes_tb(self):
        """Test format_bytes with TB."""
        from pptx_indexer.core.utils import format_bytes

        assert format_bytes(1099511627776) == "1.00 TB"

    def test_truncate_text_short(self):
        """Test truncate_text with short text."""
        from pptx_indexer.core.utils import truncate_text

        assert truncate_text("short") == "short"

    def test_truncate_text_long(self):
        """Test truncate_text with long text."""
        from pptx_indexer.core.utils import truncate_text

        result = truncate_text("this is a very long text", length=10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_truncate_text_custom_suffix(self):
        """Test truncate_text with custom suffix."""
        from pptx_indexer.core.utils import truncate_text

        result = truncate_text("very long text", length=10, suffix="[more]")
        assert result.endswith("[more]")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
