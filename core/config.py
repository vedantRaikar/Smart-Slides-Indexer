"""Application configuration using Pydantic settings.

All configuration is loaded from environment variables.
A .env file in the project root is automatically loaded.
"""

from functools import lru_cache
from typing import Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    provider: str = Field(default="groq", description="LLM provider: openai, groq, bigpickle, gemini")
    api_key: Optional[str] = Field(default=None, description="LLM API key")
    model: str = Field(default="llama-3.1-70b-versatile", description="Model name")
    temperature: float = Field(default=0.3, description="Default temperature")
    max_tokens: int = Field(default=512, description="Max tokens per request")
    base_url: Optional[str] = Field(default=None, description="Custom API base URL")
    batch_size: int = Field(default=10, description="Batch size for LLM calls")
    cache_enabled: bool = Field(default=True, description="Enable LLM response caching")


class EmbedderConfig(BaseSettings):
    """Embedder configuration."""

    provider: str = Field(default="sentence-transformers", description="Embedder provider")
    model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model")
    batch_size: int = Field(default=32, description="Batch size for embeddings")
    cache_enabled: bool = Field(default=True, description="Enable embedding caching")
    device: str = Field(default="cpu", description="Device: cpu, cuda")


class VectorStoreConfig(BaseSettings):
    """Vector store configuration."""

    provider: str = Field(default="chroma", description="Vector store provider: chroma, qdrant, pinecone")
    collection_name: str = Field(default="slides", description="Default collection name")
    persist_directory: Optional[str] = Field(default="./data/chroma", description="Chroma persist directory")
    distance_metric: str = Field(default="cosine", description="Distance metric")


class OCRConfig(BaseSettings):
    """OCR configuration."""

    provider: str = Field(default="paddleocr", description="OCR provider: paddleocr, pytesseract")
    languages: List[str] = Field(default=["en"], description="OCR languages")
    enabled: bool = Field(default=True, description="Enable OCR processing")
    use_angle_cls: bool = Field(default=True, description="Use angle classification")


class WorkerConfig(BaseSettings):
    """Worker pipeline configuration."""

    max_workers: int = Field(default=4, description="Max parallel workers")
    retry_attempts: int = Field(default=3, description="Max retry attempts")
    retry_backoff: float = Field(default=1.0, description="Exponential backoff base")
    job_timeout: int = Field(default=600, description="Job timeout in seconds")
    idempotency_enabled: bool = Field(default=True, description="Enable idempotent processing")
    artifacts_path: str = Field(default="./data/artifacts", description="Intermediate artifacts path")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format: json, console")
    output: str = Field(default="stdout", description="Log output: stdout, file")
    file_path: Optional[str] = Field(default=None, description="Log file path")


class MetricsConfig(BaseSettings):
    """Observability configuration."""

    enable_prometheus: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")
    enable_tracing: bool = Field(default=False, description="Enable OpenTelemetry tracing")
    tracing_endpoint: Optional[str] = Field(default=None, description="OTLP endpoint")


class RedisConfig(BaseSettings):
    """Redis configuration for queue/caching."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database")
    password: Optional[str] = Field(default=None, description="Redis password")
    enabled: bool = Field(default=False, description="Enable Redis")


class AppConfig(BaseSettings):
    """Main application configuration."""

    # Core settings
    app_name: str = Field(default="smart-slides-indexer", description="Application name")
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Debug mode")

    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")

    # Sub-configs
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedder: EmbedderConfig = Field(default_factory=EmbedderConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    worker: WorkerConfig = Field(default_factory=WorkerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": "__",
        "extra": "ignore",
    }


@lru_cache()
def get_config() -> AppConfig:
    """Get cached application configuration.
    
    Returns:
        AppConfig: Application configuration singleton
    """
    return AppConfig()


# =============================================================================
# Environment Variable Documentation
# =============================================================================
REQUIRED_ENV_VARS = {
    # At least one of these must be set for LLM functionality
    "OPENAI_API_KEY": "OpenAI API key (if using OpenAI provider)",
    "GROQ_API_KEY": "Groq API key (if using Groq provider)", 
    "GOOGLE_API_KEY": "Google API key (if using Gemini provider)",
    "ROUTEWAY_API_KEY": "Routeway API key (if using BigPickle provider)",
}

OPTIONAL_ENV_VARS = {
    # LLM settings
    "LLM__PROVIDER": "LLM provider (openai, groq, bigpickle, gemini)",
    "LLM__MODEL": "Model name",
    "LLM__TEMPERATURE": "LLM temperature (0.0-1.0)",
    "LLM__MAX_TOKENS": "Max tokens per request",
    "LLM__BATCH_SIZE": "Batch size for LLM calls",
    "LLM__CACHE_ENABLED": "Enable caching",
    
    # Embedder settings
    "EMBEDDER__PROVIDER": "Embedder provider",
    "EMBEDDER__MODEL": "Embedding model name",
    "EMBEDDER__BATCH_SIZE": "Batch size for embeddings",
    "EMBEDDER__DEVICE": "Device (cpu, cuda)",
    
    # Vector store settings
    "VECTOR_STORE__PROVIDER": "Vector store provider",
    "VECTOR_STORE__COLLECTION_NAME": "Collection name",
    "VECTOR_STORE__PERSIST_DIRECTORY": "Persist directory",
    
    # OCR settings
    "OCR__PROVIDER": "OCR provider (paddleocr, pytesseract)",
    "OCR__ENABLED": "Enable OCR",
    "OCR__LANGUAGES": "OCR languages (comma-separated)",
    
    # Worker settings
    "WORKER__MAX_WORKERS": "Max parallel workers",
    "WORKER__RETRY_ATTEMPTS": "Max retry attempts",
    "WORKER__IDEMPOTENCY_ENABLED": "Enable idempotent processing",
    "WORKER__ARTIFACTS_PATH": "Intermediate artifacts path",
    
    # Redis
    "REDIS__ENABLED": "Enable Redis",
    "REDIS__HOST": "Redis host",
    "REDIS__PORT": "Redis port",
    
    # API
    "API_HOST": "API host",
    "API_PORT": "API port",
    
    # Observability
    "LOGGING__LEVEL": "Log level",
    "LOGGING__FORMAT": "Log format (json, console)",
    "METRICS__ENABLE_PROMETHEUS": "Enable Prometheus",
    "METRICS__PROMETHEUS_PORT": "Prometheus port",
}
