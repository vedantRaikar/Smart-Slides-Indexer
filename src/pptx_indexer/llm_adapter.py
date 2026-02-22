"""LLM Adapter with caching and batching support.

Provides a unified interface for different LLM providers with:
- Content hash-based caching
- Batch processing for multiple prompts
- Provider abstraction (OpenAI, Groq, Gemini, BigPickle)
"""

import hashlib
import json
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from pptx_indexer.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM response with metadata."""

    text: str
    model: str
    tokens_used: Optional[int] = None
    cached: bool = False


class LLMCache:
    """File-based LLM response cache with thread safety."""

    def __init__(self, cache_dir: str = "./data/cache/llm"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _get_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters."""
        key_data = {
            "prompt": prompt,
            "model": model,
            "kwargs": kwargs,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, prompt: str, model: str, **kwargs) -> Optional[LLMResponse]:
        """Get cached response if available."""
        key = self._get_cache_key(prompt, model, **kwargs)
        cache_file = self.cache_dir / f"{key}.json"

        with self._lock:
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text())
                    logger.debug(f"Cache hit for prompt hash: {key[:8]}...")
                    return LLMResponse(
                        text=data["text"],
                        model=data["model"],
                        tokens_used=data.get("tokens_used"),
                        cached=True,
                    )
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Corrupted cache file: {e}")
        return None

    def set(self, response: LLMResponse, prompt: str, **kwargs):
        """Store response in cache."""
        key = self._get_cache_key(prompt, response.model, **kwargs)
        cache_file = self.cache_dir / f"{key}.json"

        with self._lock:
            data = {
                "text": response.text,
                "model": response.model,
                "tokens_used": response.tokens_used,
            }
            cache_file.write_text(json.dumps(data))

    def _get_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters."""
        key_data = {
            "prompt": prompt,
            "model": model,
            "kwargs": kwargs,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()


class BaseLLMAdapter(ABC):
    """Abstract base class for LLM adapters."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a single response."""
        pass

    @abstractmethod
    def batch_generate(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Get model name."""
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI LLM adapter."""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        import openai

        openai.api_key = api_key
        self._client = openai
        self._model = model
        self._kwargs = kwargs
        logger.info(f"Initialized OpenAI adapter: {model}")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        try:
            response = self._client.ChatCompletion.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 512),
            )
            return LLMResponse(
                text=response.choices[0].message.content.strip(),
                model=self._model,
                tokens_used=response.usage.total_tokens if hasattr(response, "usage") else None,
            )
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    def batch_generate(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        return [self.generate(p, **kwargs) for p in prompts]

    @property
    def model(self) -> str:
        return self._model


class GroqAdapter(BaseLLMAdapter):
    """Groq LLM adapter (OpenAI-compatible)."""

    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile", **kwargs):
        from openai import OpenAI

        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self._model = model
        self._kwargs = kwargs
        logger.info(f"Initialized Groq adapter: {model}")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 512),
            )
            return LLMResponse(
                text=response.choices[0].message.content.strip(),
                model=self._model,
                tokens_used=response.usage.total_tokens if hasattr(response, "usage") else None,
            )
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise

    def batch_generate(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        return [self.generate(p, **kwargs) for p in prompts]

    @property
    def model(self) -> str:
        return self._model


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini LLM adapter."""

    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._client = genai
        self._model = model
        self._kwargs = kwargs
        logger.info(f"Initialized Gemini adapter: {model}")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        try:
            model = self._client.GenerativeModel(self._model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": kwargs.get("temperature", 0.3),
                    "max_output_tokens": kwargs.get("max_tokens", 512),
                },
            )
            return LLMResponse(
                text=response.text.strip(),
                model=self._model,
            )
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    def batch_generate(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        return [self.generate(p, **kwargs) for p in prompts]

    @property
    def model(self) -> str:
        return self._model


class BigPickleAdapter(BaseLLMAdapter):
    """BigPickle (GLM-4.6) LLM adapter via Routeway."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.6:free",
        base_url: str = "https://api.routeway.ai/v1",
        **kwargs,
    ):
        if not api_key:
            logger.warning("BigPickle: No API key provided")
            self._client = None
            self._model = model
            return

        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._kwargs = kwargs
        logger.info(f"Initialized BigPickle adapter: {model}")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        if self._client is None:
            raise RuntimeError("BigPickle not initialized: no API key")
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 512),
            )
            return LLMResponse(
                text=response.choices[0].message.content.strip(),
                model=self._model,
            )
        except Exception as e:
            logger.error(f"BigPickle generation failed: {e}")
            raise

    def batch_generate(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        return [self.generate(p, **kwargs) for p in prompts]

    @property
    def model(self) -> str:
        return self._model


class LLMAdapter:
    """Unified LLM adapter with caching and batching.

    Usage:
        adapter = LLMAdapter()
        response = adapter.generate("Explain coupling in software")

        # Batch processing
        responses = adapter.batch_generate([
            "What is data coupling?",
            "What is stamp coupling?",
        ])
    """

    ADAPTERS = {
        "openai": OpenAIAdapter,
        "groq": GroqAdapter,
        "gemini": GeminiAdapter,
        "bigpickle": BigPickleAdapter,
    }

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        cache_enabled: bool = True,
        batch_size: int = 10,
        **kwargs,
    ):
        config = get_config()

        self.provider = provider or config.llm.provider
        self.model = model or config.llm.model
        self.batch_size = batch_size or config.llm.batch_size

        # Get API key from environment if not provided
        if not api_key:
            api_key = self._get_api_key(self.provider)

        self._adapter = self._create_adapter(api_key, **kwargs)
        self._cache = LLMCache() if cache_enabled and config.llm.cache_enabled else None

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key from environment variables."""
        import os

        key_map = {
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "bigpickle": "ROUTEWAY_API_KEY",
        }
        return os.getenv(key_map.get(provider, ""))

    def _create_adapter(self, api_key: str, **kwargs) -> BaseLLMAdapter:
        """Create the underlying adapter."""
        adapter_class = self.ADAPTERS.get(self.provider.lower())
        if not adapter_class:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        if api_key:
            return adapter_class(api_key=api_key, model=self.model, **kwargs)

        # Fallback to BigPickle without key
        if self.provider == "bigpickle":
            return BigPickleAdapter(api_key=None, model=self.model)

        raise ValueError(f"API key required for {self.provider}")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a single response with optional caching."""
        # Check cache
        if self._cache:
            cached = self._cache.get(prompt, self.model, **kwargs)
            if cached:
                return cached

        # Generate
        response = self._adapter.generate(prompt, **kwargs)

        # Cache result
        if self._cache:
            self._cache.set(response, prompt, **kwargs)

        return response

    def batch_generate(
        self,
        prompts: List[str],
        use_cache: bool = True,
        **kwargs,
    ) -> List[LLMResponse]:
        """Generate responses for multiple prompts with optional caching.

        Args:
            prompts: List of prompts to process
            use_cache: Whether to check/use cache
            **kwargs: Additional parameters passed to generate

        Returns:
            List of LLMResponse objects
        """
        results = []

        for prompt in prompts:
            if use_cache and self._cache:
                cached = self._cache.get(prompt, self.model, **kwargs)
                if cached:
                    results.append(cached)
                    continue

            response = self._adapter.generate(prompt, **kwargs)
            results.append(response)

            if use_cache and self._cache:
                self._cache.set(response, prompt, **kwargs)

        return results

    @property
    def model(self) -> str:
        return self._adapter.model


def create_llm_adapter(**kwargs) -> LLMAdapter:
    """Factory function to create LLM adapter from config."""
    return LLMAdapter(**kwargs)
