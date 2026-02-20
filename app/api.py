"""
FastAPI endpoints for AutoML GenAI service.
"""

from typing import Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
from loguru import logger

from .service import AutoMLGenAIService
from .pipeline import ExecutionResult


# Pydantic models for API
class ModelConfigInput(BaseModel):
    """Input model for model configuration."""
    name: str
    provider: str
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 2048
    custom_params: dict = {}


class PipelineCreateRequest(BaseModel):
    """Request to create a pipeline."""
    name: str
    models: List[ModelConfigInput]
    routing_strategy: str = "random"
    cache_results: bool = True


class ExecuteRequest(BaseModel):
    """Request to execute a pipeline."""
    prompt: str
    model_name: Optional[str] = None
    stream: bool = False


class BatchExecuteRequest(BaseModel):
    """Request to batch execute."""
    prompts: List[str]
    parallel: bool = True


class PromptOptimizeRequest(BaseModel):
    """Request to optimize a prompt."""
    prompt: str
    strategy: str = "iterative"


class ExecutionResponse(BaseModel):
    """Response from execution."""
    model_used: str
    output: str
    latency: float
    success: bool
    error: Optional[str] = None


# Initialize FastAPI app and service
app = FastAPI(
    title="AutoML GenAI Service",
    description="Auto-tuning service for generative AI models",
    version="0.1.0",
)

service = AutoMLGenAIService()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    service.close()
    logger.info("Service shutdown completed")


# Pipeline endpoints
@app.post("/pipelines")
async def create_pipeline(request: PipelineCreateRequest) -> dict:
    """Create a new AutoML pipeline."""
    try:
        models_data = [model.dict() for model in request.models]
        pipeline_id = service.create_pipeline(
            name=request.name,
            models=models_data,
            routing_strategy=request.routing_strategy,
            cache_results=request.cache_results,
        )
        return {
            "pipeline_id": pipeline_id,
            "name": request.name,
            "models_count": len(models_data),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pipelines")
async def list_pipelines() -> dict:
    """List all pipelines."""
    pipelines = service.list_pipelines()
    return {"pipelines": pipelines, "count": len(pipelines)}


@app.get("/pipelines/{pipeline_id}")
async def get_pipeline_config(pipeline_id: str) -> dict:
    """Get pipeline configuration."""
    try:
        config = service.export_pipeline_config(pipeline_id)
        return {"pipeline_id": pipeline_id, "config": config}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Execution endpoints
@app.post("/pipelines/{pipeline_id}/execute")
async def execute_pipeline(
    pipeline_id: str,
    request: ExecuteRequest,
) -> ExecutionResponse:
    """Execute a pipeline."""
    try:
        result = await service.execute(
            pipeline_id=pipeline_id,
            prompt=request.prompt,
            model_name=request.model_name,
            stream=request.stream,
        )
        return ExecutionResponse(
            model_used=result.model_used,
            output=result.output,
            latency=result.latency,
            success=result.success,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pipelines/{pipeline_id}/batch-execute")
async def batch_execute_pipeline(
    pipeline_id: str,
    request: BatchExecuteRequest,
) -> dict:
    """Execute multiple prompts in batch."""
    try:
        results = await service.batch_execute(
            pipeline_id=pipeline_id,
            prompts=request.prompts,
            parallel=request.parallel,
        )
        return {
            "pipeline_id": pipeline_id,
            "total_prompts": len(request.prompts),
            "successful": sum(1 for r in results if r.success),
            "results": [
                {
                    "output": r.output,
                    "model": r.model_used,
                    "latency": r.latency,
                }
                for r in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Monitoring endpoints
@app.get("/pipelines/{pipeline_id}/metrics")
async def get_metrics(pipeline_id: str) -> dict:
    """Get pipeline metrics."""
    try:
        metrics = service.get_pipeline_metrics(pipeline_id)
        return {"pipeline_id": pipeline_id, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/pipelines/{pipeline_id}/history")
async def get_history(
    pipeline_id: str,
    limit: int = 100,
) -> dict:
    """Get execution history."""
    try:
        history = service.get_execution_history(pipeline_id, limit)
        return {"pipeline_id": pipeline_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/pipelines/{pipeline_id}/stats")
async def get_stats(pipeline_id: str) -> dict:
    """Get performance statistics."""
    try:
        stats = service.get_performance_stats(pipeline_id)
        return {"pipeline_id": pipeline_id, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Optimization endpoints
@app.post("/optimize-prompt")
async def optimize_prompt(request: PromptOptimizeRequest) -> dict:
    """Optimize a prompt using auto-techniques."""
    try:
        optimized = service.optimize_prompt(
            prompt=request.prompt,
            strategy=request.strategy,
        )
        return {
            "original": request.prompt,
            "optimized": optimized,
            "strategy": request.strategy,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "pipelines": len(service.list_pipelines()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
