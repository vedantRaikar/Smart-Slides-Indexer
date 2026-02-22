"""Tests for schema models - minimal dependencies."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest


class TestNodeEnums:
    """Tests for enum types."""

    def test_node_type_values(self):
        """Test NodeType enum values."""
        from pptx_indexer.schemas.slide_node import NodeType

        assert NodeType.SLIDE.value == "slide"
        assert NodeType.SECTION.value == "section"
        assert NodeType.CONCEPT.value == "concept"
        assert NodeType.IMAGE.value == "image"
        assert NodeType.TABLE.value == "table"

    def test_content_type_values(self):
        """Test ContentType enum values."""
        from pptx_indexer.schemas.slide_node import ContentType

        assert ContentType.TITLE.value == "title"
        assert ContentType.BULLET.value == "bullet"
        assert ContentType.TEXT.value == "text"
        assert ContentType.IMAGE.value == "image"
        assert ContentType.TABLE.value == "table"


class TestBulletPoint:
    """Tests for BulletPoint schema."""

    def test_bullet_point_creation(self):
        """Test BulletPoint creation."""
        from pptx_indexer.schemas.slide_node import BulletPoint

        bullet = BulletPoint(text="Test bullet", level=0, index=0)
        assert bullet.text == "Test bullet"
        assert bullet.level == 0
        assert bullet.index == 0
        assert bullet.keywords == []

    def test_bullet_point_to_dict(self):
        """Test BulletPoint serialization."""
        from pptx_indexer.schemas.slide_node import BulletPoint

        bullet = BulletPoint(text="Test", level=1, index=2, keywords=["test", "key"])
        result = bullet.to_dict()
        assert result["text"] == "Test"
        assert result["level"] == 1
        assert result["index"] == 2
        assert result["keywords"] == ["test", "key"]


class TestImageNode:
    """Tests for ImageNode schema."""

    def test_image_node_creation(self):
        """Test ImageNode creation."""
        from pptx_indexer.schemas.slide_node import ImageNode

        image = ImageNode(image_id="img-1", image_path="/path/to/image.png")
        assert image.image_id == "img-1"
        assert image.image_path == "/path/to/image.png"
        assert image.caption is None
        assert image.ocr_text is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
