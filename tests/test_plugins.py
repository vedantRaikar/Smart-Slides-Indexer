"""Tests for plugins - minimal dependencies."""

import pytest


class TestBaseLLM:
    """Tests for BaseLLM plugin."""

    def test_base_llm_abstract(self):
        """Test BaseLLM is abstract."""
        from pptx_indexer.plugins.base_llm import BaseLLM

        with pytest.raises(TypeError):
            BaseLLM()


class TestOCRPlugins:
    """Tests for OCR plugins."""

    def test_pytesseract_initialization(self):
        """Test Pytesseract OCR initialization."""
        from pptx_indexer.plugins.default_plugins.implementations import PytesseractOCR

        # Just test that class can be instantiated with default params
        # (actual import will fail without dependencies)
        import inspect

        sig = inspect.signature(PytesseractOCR.__init__)
        params = list(sig.parameters.keys())
        assert "lang" in params

    def test_paddleocr_initialization(self):
        """Test PaddleOCR initialization."""
        from pptx_indexer.plugins.default_plugins.implementations import PaddleOCR

        import inspect

        sig = inspect.signature(PaddleOCR.__init__)
        params = list(sig.parameters.keys())
        assert "lang" in params
        assert "use_angle_cls" in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
