"""Shared fixtures for tests."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_pptx_path(temp_dir):
    """Create a mock PPTX file path."""
    return os.path.join(temp_dir, "test.pptx")


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock()
    config.app_name = "test-app"
    config.environment = "test"
    config.llm.provider = "groq"
    config.llm.model = "test-model"
    config.embedder.model = "test-embedder"
    config.vector_store.provider = "chroma"
    return config


@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = Mock()
    llm.generate.return_value = "Generated text"
    llm.batch_generate.return_value = ["Response 1", "Response 2"]
    return llm


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = Mock()
    store.add_documents = Mock()
    store.search.return_value = []
    store.delete_collection = Mock()
    return store


@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_slides():
    """Create sample slide nodes for testing."""
    from pptx_indexer.schemas.slide_node import (
        BulletPoint,
        ImageNode,
        SlideNode,
        ContentType,
    )

    return [
        SlideNode(
            slide_number=1,
            title="Introduction",
            content_type=ContentType.TITLE,
            bullets=[
                BulletPoint(text="Welcome", level=0, index=0),
                BulletPoint(text="Overview", level=0, index=1),
            ],
        ),
        SlideNode(
            slide_number=2,
            title="Main Content",
            content_type=ContentType.TEXT,
            bullets=[
                BulletPoint(text="Point 1", level=0, index=0),
                BulletPoint(text="Sub point", level=1, index=1),
            ],
            images=[ImageNode(image_id="img-1", image_path="/test.png")],
        ),
    ]


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    return {
        "slide_1": [0.1] * 384,
        "slide_2": [0.2] * 384,
    }
