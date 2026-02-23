"""Tests for plugins - simplified."""

import pytest


class TestLLMImplementations:
    """Tests for LLM implementations."""

    def test_bigpickle_llm_no_api_key(self):
        """Test BigPickleLLM without API key."""
        from pptx_indexer.plugins.default_plugins.implementations import BigPickleLLM

        llm = BigPickleLLM(api_key=None)
        assert llm.client is None


class TestOCRImplementations:
    """Tests for OCR implementations."""

    def test_pytesseract_initialization(self):
        """Test PytesseractOCR initialization."""
        from pptx_indexer.plugins.default_plugins.implementations import PytesseractOCR

        ocr = PytesseractOCR()
        assert ocr is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
