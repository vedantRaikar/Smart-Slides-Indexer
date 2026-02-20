"""Main AutoML GenAI service."""

from typing import Optional, List, Dict, Any
import uuid
from loguru import logger

from .config import (
    PipelineConfig,
    ModelConfig,
    ModelProvider,
    PromptTemplate,
)
from .pipeline import AutoMLPipeline, ExecutionResult
from .storage import StorageManager
from .optimizer import PromptOptimizer


class AutoMLGenAIService:
    """Main service for AutoML GenAI operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.storage = StorageManager(database_url)
        self.pipelines: Dict[str, AutoMLPipeline] = {}
        logger.info("AutoML GenAI Service initialized")
    
    def create_pipeline(
        self,
        name: str,
        models: List[Dict[str, Any]],
        prompts: Optional[List[Dict[str, Any]]] = None,
        routing_strategy: str = "random",
        cache_results: bool = True,
    ) -> str:
        """Create a new AutoML pipeline."""
        try:
            pipeline_id = str(uuid.uuid4())
            
            # Build model configs
            model_configs = []
            for model_data in models:
                config = ModelConfig(
                    name=model_data.get("name"),
                    provider=ModelProvider(model_data.get("provider", "openai")),
                    model_id=model_data.get("model_id"),
                    temperature=model_data.get("temperature", 0.7),
                    max_tokens=model_data.get("max_tokens", 2048),
                    custom_params=model_data.get("custom_params", {}),
                )
                model_configs.append(config)
            
            # Build prompt configs
            prompt_configs = []
            if prompts:
                for prompt_data in prompts:
                    config = PromptTemplate(
                        name=prompt_data.get("name"),
                        template=prompt_data.get("template"),
                        variables=prompt_data.get("variables", []),
                        optimization_metrics=prompt_data.get(
                            "optimization_metrics",
                            ["accuracy", "latency"]
                        ),
                    )
                    prompt_configs.append(config)
            
            # Create pipeline config
            pipeline_config = PipelineConfig(
                name=name,
                models=model_configs,
                prompts=prompt_configs,
                routing_strategy=routing_strategy,
                cache_results=cache_results,
            )
            
            # Initialize pipeline
            pipeline = AutoMLPipeline(pipeline_config)
            self.pipelines[pipeline_id] = pipeline
            
            # Save to storage
            self.storage.save_pipeline_config(
                pipeline_id,
                name,
                {
                    "models": [m.dict() for m in model_configs],
                    "routing_strategy": routing_strategy,
                    "cache_results": cache_results,
                }
            )
            
            logger.info(f"Created pipeline: {pipeline_id} ({name})")
            return pipeline_id
            
        except Exception as e:
            logger.error(f"Failed to create pipeline: {e}")
            raise
    
    async def execute(
        self,
        pipeline_id: str,
        prompt: str,
        model_name: Optional[str] = None,
        stream: bool = False,
    ) -> ExecutionResult:
        """Execute a pipeline with a prompt."""
        try:
            if pipeline_id not in self.pipelines:
                raise ValueError(f"Pipeline not found: {pipeline_id}")
            
            pipeline = self.pipelines[pipeline_id]
            result = await pipeline.execute(
                prompt=prompt,
                model_name=model_name,
                stream=stream,
            )
            
            # Save result
            self.storage.save_execution(
                execution_id=str(uuid.uuid4()),
                pipeline_id=pipeline_id,
                model_used=result.model_used,
                prompt=prompt,
                output=result.output,
                latency=result.latency,
                cost=result.cost,
                tokens_used=result.tokens_used,
                success=result.success,
                error_message=result.error,
                metadata=result.metadata,
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
    
    async def batch_execute(
        self,
        pipeline_id: str,
        prompts: List[str],
        parallel: bool = True,
    ) -> List[ExecutionResult]:
        """Execute multiple prompts."""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        
        pipeline = self.pipelines[pipeline_id]
        return await pipeline.batch_execute(prompts, parallel)
    
    def get_pipeline_metrics(self, pipeline_id: str) -> Dict[str, Any]:
        """Get metrics for a pipeline."""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        
        pipeline = self.pipelines[pipeline_id]
        return pipeline.get_metrics()
    
    def get_execution_history(
        self,
        pipeline_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get execution history."""
        return self.storage.get_execution_history(pipeline_id, limit)
    
    def get_performance_stats(self, pipeline_id: str) -> Dict[str, Any]:
        """Get performance statistics."""
        return self.storage.get_performance_stats(pipeline_id)
    
    def optimize_prompt(
        self,
        prompt: str,
        strategy: str = "iterative",
    ) -> str:
        """Optimize a prompt using various strategies."""
        optimizer = PromptOptimizer()
        return optimizer.optimize_prompt(prompt, strategy)
    
    def list_pipelines(self) -> List[str]:
        """List all pipeline IDs."""
        return list(self.pipelines.keys())
    
    def export_pipeline_config(self, pipeline_id: str) -> str:
        """Export pipeline configuration."""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        
        return self.pipelines[pipeline_id].export_config()
    
    def close(self) -> None:
        """Close service and cleanup."""
        self.storage.close()
        logger.info("AutoML GenAI Service closed")
