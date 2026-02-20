"""AutoML pipeline orchestration and execution."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio
from loguru import logger

from .config import PipelineConfig, ModelConfig
from .models import ModelFactory, BaseLLMModel
from .optimizer import PromptOptimizer


@dataclass
class ExecutionResult:
    """Result of a pipeline execution."""
    prompt: str
    output: str
    model_used: str
    latency: float
    cost: float = 0.0
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None


class AutoMLPipeline:
    """Main orchestrator for AutoML GenAI pipelines."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.models: Dict[str, BaseLLMModel] = {}
        self.optimizer = PromptOptimizer(
            target_metrics=config.prompts[0].optimization_metrics if config.prompts else None
        )
        self.execution_history: List[ExecutionResult] = []
        self.cache: Dict[str, str] = {}
        
        self._initialize_models()
        logger.info(f"Initialized AutoML pipeline: {config.name}")
    
    def _initialize_models(self) -> None:
        """Initialize all models in pipeline."""
        for model_config in self.config.models:
            try:
                model = ModelFactory.create(model_config)
                self.models[model_config.name] = model
                logger.info(f"Loaded model: {model_config.name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_config.name}: {e}")
    
    async def execute(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        use_optimization: bool = True,
        stream: bool = False,
    ) -> ExecutionResult:
        """Execute pipeline with given prompt."""
        
        if not self.models:
            raise ValueError("No models available in pipeline")
        
        # Check cache
        cache_key = f"{prompt}:{model_name}"
        if self.config.cache_results and cache_key in self.cache:
            logger.debug("Cache hit")
            return ExecutionResult(
                prompt=prompt,
                output=self.cache[cache_key],
                model_used=model_name or "cached",
                latency=0.0,
                metadata={"source": "cache"}
            )
        
        # Optimize prompt if enabled
        optimized_prompt = prompt
        if use_optimization:
            optimized_prompt = self.optimizer.optimize_prompt(prompt)
            logger.debug("Prompt optimized")
        
        # Select model
        selected_model_name = model_name or self._select_model()
        selected_model = self.models[selected_model_name]
        
        # Execute
        try:
            import time
            start_time = time.time()
            
            if stream:
                output = await self._stream_execution(selected_model, optimized_prompt)
            else:
                output = await selected_model.generate(optimized_prompt)
            
            latency = time.time() - start_time
            
            result = ExecutionResult(
                prompt=prompt,
                output=output,
                model_used=selected_model_name,
                latency=latency,
                success=True,
            )
            
            # Cache result
            if self.config.cache_results:
                self.cache[cache_key] = output
            
            # Log result
            if self.config.log_results:
                self.execution_history.append(result)
            
            logger.info(f"Pipeline execution completed: {selected_model_name} ({latency:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return ExecutionResult(
                prompt=prompt,
                output="",
                model_used=selected_model_name,
                latency=0.0,
                success=False,
                error=str(e),
            )
    
    async def _stream_execution(self, model: BaseLLMModel, prompt: str) -> str:
        """Execute with streaming output."""
        output = ""
        async for chunk in model.stream_generate(prompt):
            output += chunk
        return output
    
    def _select_model(self) -> str:
        """Select model based on routing strategy."""
        strategy = self.config.routing_strategy
        model_names = list(self.models.keys())
        
        if strategy == "round_robin":
            # Simple round-robin
            idx = len(self.execution_history) % len(model_names)
            return model_names[idx]
        
        elif strategy == "cost_optimized":
            # Select cheapest model (would need pricing data)
            return model_names[0]
        
        else:  # random
            import random
            return random.choice(model_names)
    
    async def batch_execute(
        self,
        prompts: List[str],
        parallel: bool = True,
    ) -> List[ExecutionResult]:
        """Execute multiple prompts."""
        if parallel:
            tasks = [self.execute(prompt) for prompt in prompts]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for prompt in prompts:
                result = await self.execute(prompt)
                results.append(result)
            return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics."""
        if not self.execution_history:
            return {"status": "No executions"}
        
        results = [r for r in self.execution_history if r.success]
        if not results:
            return {"status": "All executions failed"}
        
        latencies = [r.latency for r in results]
        
        return {
            "total_executions": len(self.execution_history),
            "successful_executions": len(results),
            "failure_rate": (len(self.execution_history) - len(results)) / len(self.execution_history),
            "average_latency": sum(latencies) / len(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "cache_size": len(self.cache),
            "optimizer_report": self.optimizer.get_optimization_report(),
        }
    
    def export_config(self) -> str:
        """Export pipeline configuration."""
        return json.dumps(
            {
                "name": self.config.name,
                "models": [
                    {
                        "name": m.name,
                        "provider": m.provider.value,
                        "model_id": m.model_id,
                    }
                    for m in self.config.models
                ],
                "routing_strategy": self.config.routing_strategy,
                "caching_enabled": self.config.cache_results,
            },
            indent=2,
        )
