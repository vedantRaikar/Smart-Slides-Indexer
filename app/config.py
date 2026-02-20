"""Configuration management for AutoML GenAI service."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"


class ModelConfig(BaseModel):
    """Model configuration."""
    name: str
    provider: ModelProvider
    model_id: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    timeout: int = Field(default=30, ge=1)
    retry_count: int = Field(default=3, ge=1)
    custom_params: Dict[str, Any] = Field(default_factory=dict)


class PromptTemplate(BaseModel):
    """Prompt template for optimization."""
    name: str
    template: str
    variables: list[str]
    optimization_metrics: list[str] = Field(
        default=["accuracy", "latency", "cost"]
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineConfig(BaseModel):
    """Pipeline execution configuration."""
    name: str
    models: list[ModelConfig]
    prompts: list[PromptTemplate]
    use_routing: bool = False
    routing_strategy: str = "random"  # random, round_robin, cost_optimized
    timeout: int = Field(default=60, ge=1)
    retry_strategy: str = "exponential"
    cache_results: bool = True
    log_results: bool = True


class Settings(BaseSettings):
    """Application settings from environment."""
    
    # API Keys
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Database
    database_url: str = "sqlite:///automl.db"
    
    # Service
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
