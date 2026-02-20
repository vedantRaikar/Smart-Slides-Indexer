"""LLM model management and abstraction layer."""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from loguru import logger
from .config import ModelConfig, ModelProvider


class BaseLLMModel(ABC):
    """Abstract base class for LLM models."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        **kwargs
    ):
        """Stream text generation."""
        pass


class OpenAIModel(BaseLLMModel):
    """OpenAI GPT model wrapper."""
    
    def _initialize_client(self) -> None:
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.config.custom_params.get("api_key"))
            logger.info(f"Initialized OpenAI client for {self.config.model_id}")
        except ImportError:
            logger.error("openai package not installed")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate text using OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                timeout=self.config.timeout,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def stream_generate(
        self,
        prompt: str,
        **kwargs
    ):
        """Stream text generation from OpenAI."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                timeout=self.config.timeout,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise


class AnthropicModel(BaseLLMModel):
    """Anthropic Claude model wrapper."""
    
    def _initialize_client(self) -> None:
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.config.custom_params.get("api_key"))
            logger.info(f"Initialized Anthropic client for {self.config.model_id}")
        except ImportError:
            logger.error("anthropic package not installed")
            raise
    
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate text using Anthropic API."""
        try:
            message = await self.client.messages.create(
                model=self.config.model_id,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.config.timeout,
                **kwargs
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise
    
    async def stream_generate(
        self,
        prompt: str,
        **kwargs
    ):
        """Stream text generation from Anthropic."""
        try:
            async with self.client.messages.stream(
                model=self.config.model_id,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.config.timeout,
                **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            raise


class GoogleModel(BaseLLMModel):
    """Google Generative AI model wrapper."""
    
    def _initialize_client(self) -> None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.custom_params.get("api_key"))
            self.client = genai.GenerativeModel(self.config.model_id)
            logger.info(f"Initialized Google client for {self.config.model_id}")
        except ImportError:
            logger.error("google-generativeai package not installed")
            raise
    
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate text using Google AI API."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.config.temperature,
                        "max_output_tokens": self.config.max_tokens,
                        **kwargs
                    }
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Google generation failed: {e}")
            raise
    
    async def stream_generate(
        self,
        prompt: str,
        **kwargs
    ):
        """Stream text generation from Google."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.generate_content(
                    prompt,
                    stream=True,
                    generation_config={
                        "temperature": self.config.temperature,
                        "max_output_tokens": self.config.max_tokens,
                        **kwargs
                    }
                )
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Google streaming failed: {e}")
            raise


class ModelFactory:
    """Factory for creating model instances."""
    
    _models = {
        ModelProvider.OPENAI: OpenAIModel,
        ModelProvider.ANTHROPIC: AnthropicModel,
        ModelProvider.GOOGLE: GoogleModel,
    }
    
    @classmethod
    def create(cls, config: ModelConfig) -> BaseLLMModel:
        """Create a model instance based on config."""
        model_class = cls._models.get(config.provider)
        if not model_class:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        logger.debug(f"Creating model: {config.name} ({config.provider})")
        return model_class(config)
    
    @classmethod
    def register(cls, provider: ModelProvider, model_class: type) -> None:
        """Register a new model provider."""
        cls._models[provider] = model_class
        logger.info(f"Registered model provider: {provider}")
