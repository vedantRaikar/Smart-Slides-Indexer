"""Tests for plugins and default implementations."""

import pytest


class TestBaseLLM:
    """Tests for BaseLLM."""

    def test_base_llm_abstract(self):
        """Test BaseLLM is abstract."""
        from pptx_indexer.plugins.base_llm import BaseLLM
        import inspect

        assert inspect.isabstract(BaseLLM)


class TestDefaultPlugins:
    """Tests for default plugin implementations."""

    def test_pytesseract_initialization(self):
        """Test pytesseract plugin initialization."""
        from pptx_indexer.plugins.default_plugins.implementations import PytesseractOCR

        ocr = PytesseractOCR()
        assert ocr.extract_text is not None


class TestOCRPlugins:
    """Tests for OCR plugins."""

    def test_pytesseract_has_extract_method(self):
        """Test pytesseract has extract method."""
        from pptx_indexer.plugins.default_plugins.implementations import PytesseractOCR

        ocr = PytesseractOCR()
        assert hasattr(ocr, "extract_text")
        assert callable(ocr.extract_text)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
