"""
AutoML GenAI Service - Main entry point with examples.
"""

import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

from .service import AutoMLGenAIService
from .config import ModelProvider

# Load environment variables
load_dotenv()


async def example_basic_pipeline():
    """Example: Create and use a basic pipeline."""
    logger.info("=== Example 1: Basic Pipeline ===")
    
    service = AutoMLGenAIService()
    
    # Define models
    models = [
        {
            "name": "gpt-4",
            "provider": "openai",
            "model_id": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 2048,
            "custom_params": {"api_key": os.getenv("OPENAI_API_KEY")},
        },
        {
            "name": "claude-3",
            "provider": "anthropic",
            "model_id": "claude-3-opus-20240229",
            "temperature": 0.8,
            "max_tokens": 2048,
            "custom_params": {"api_key": os.getenv("ANTHROPIC_API_KEY")},
        },
    ]
    
    # Create pipeline
    pipeline_id = service.create_pipeline(
        name="content-generation-pipeline",
        models=models,
        routing_strategy="random",
        cache_results=True,
    )
    logger.info(f"Created pipeline: {pipeline_id}")
    
    # Execute with a prompt
    prompt = "Write a professional summary about artificial intelligence in 100 words"
    result = await service.execute(pipeline_id, prompt)
    
    logger.info(f"Model used: {result.model_used}")
    logger.info(f"Latency: {result.latency:.2f}s")
    logger.info(f"Output: {result.output[:200]}...")
    
    service.close()


async def example_prompt_optimization():
    """Example: Optimize prompts for better results."""
    logger.info("=== Example 2: Prompt Optimization ===")
    
    service = AutoMLGenAIService()
    
    # Original prompt
    original = "Write something about AI"
    
    # Auto-optimize using different strategies
    iterative = service.optimize_prompt(original, strategy="iterative")
    cot = service.optimize_prompt(original, strategy="chain_of_thought")
    few_shot = service.optimize_prompt(original, strategy="few_shot")
    
    logger.info(f"Original: {original}")
    logger.info(f"Iterative: {iterative}")
    logger.info(f"CoT: {cot}")
    logger.info(f"Few-shot: {few_shot}")
    
    service.close()


async def example_batch_processing():
    """Example: Process multiple prompts efficiently."""
    logger.info("=== Example 3: Batch Processing ===")
    
    service = AutoMLGenAIService()
    
    models = [
        {
            "name": "gpt-3.5",
            "provider": "openai",
            "model_id": "gpt-3.5-turbo",
            "custom_params": {"api_key": os.getenv("OPENAI_API_KEY")},
        },
    ]
    
    pipeline_id = service.create_pipeline(
        name="batch-processing",
        models=models,
    )
    
    # Multiple prompts
    prompts = [
        "Summarize quantum computing",
        "Explain blockchain technology",
        "Describe machine learning",
    ]
    
    results = await service.batch_execute(pipeline_id, prompts, parallel=True)
    
    for i, result in enumerate(results):
        logger.info(f"Prompt {i+1}: {result.output[:100]}...")
    
    service.close()


async def example_monitoring():
    """Example: Monitor pipeline performance."""
    logger.info("=== Example 4: Monitoring & Metrics ===")
    
    service = AutoMLGenAIService()
    
    models = [
        {
            "name": "gpt-4",
            "provider": "openai",
            "model_id": "gpt-4-turbo-preview",
            "custom_params": {"api_key": os.getenv("OPENAI_API_KEY")},
        },
    ]
    
    pipeline_id = service.create_pipeline(
        name="monitoring-pipeline",
        models=models,
    )
    
    # Execute some operations
    for i in range(3):
        await service.execute(pipeline_id, f"Test prompt {i+1}")
    
    # Get metrics
    metrics = service.get_pipeline_metrics(pipeline_id)
    logger.info(f"Metrics: {metrics}")
    
    # Get history
    history = service.get_execution_history(pipeline_id)
    logger.info(f"Execution history: {history}")
    
    # Get performance stats
    stats = service.get_performance_stats(pipeline_id)
    logger.info(f"Performance stats: {stats}")
    
    service.close()


async def main():
    """Main entry point."""
    logger.info("Starting AutoML GenAI Service")
    
    # Run examples (comment out those you don't want to run)
    try:
        # await example_basic_pipeline()
        await example_prompt_optimization()
        # await example_batch_processing()
        # await example_monitoring()
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
