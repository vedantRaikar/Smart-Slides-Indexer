"""
AutoML GenAI Service Package.

An intelligent service for auto-tuning and managing generative AI models.
"""

__version__ = "0.1.0"
__author__ = "AutoML Team"
__description__ = "Auto-tuning service for generative AI models"

from .service import AutoMLGenAIService
from .config import ModelConfig, PipelineConfig, ModelProvider
from .pipeline import AutoMLPipeline, ExecutionResult
from .optimizer import PromptOptimizer

__all__ = [
    "AutoMLGenAIService",
    "AutoMLPipeline",
    "PromptOptimizer",
    "ModelConfig",
    "PipelineConfig",
    "ModelProvider",
    "ExecutionResult",
]
