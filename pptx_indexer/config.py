"""Global configuration for PPTX indexer."""

from dataclasses import dataclass, field


@dataclass
class IndexingConfig:
    """Configuration for indexing pipeline."""

    # LLM Configuration
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 512

    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_batch_size: int = 32

    # OCR Configuration
    enable_ocr: bool = True
    ocr_languages: list[str] = field(default_factory=lambda: ["eng"])

    # Image Captioning
    enable_image_captions: bool = True
    caption_model: str = "blip-image-captioning-base"

    # Processing
    max_workers: int = 4
    timeout_seconds: int = 300

    # Output
    output_format: str = "json"  # json, dict, pickle
    export_embeddings: bool = True
    export_graph: bool = True

    # Chunking (None = disabled, which we do instead of chunking)
    enable_chunking: bool = False
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Advanced
    compute_similarity_matrix: bool = True
    cluster_concepts: bool = True
    max_clusters: int = 10
    generate_summaries: bool = True
