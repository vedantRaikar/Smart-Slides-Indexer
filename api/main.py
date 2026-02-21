"""FastAPI service for Smart Slides Indexer.

Provides REST API for:
- Upload and index PPTX files
- Check indexing job status
- Semantic search across indexed presentations
- Health checks and metrics
"""

import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.config import get_config
from core.llm_adapter import create_llm_adapter
from core.vector_store import create_vector_store
from workers.indexing import IndexerWorker

logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="Smart Slides Indexer API",
    description="API for indexing and semantic search of PowerPoint presentations",
    version="1.0.0",
)

# Global state
jobs: Dict[str, Dict] = {}
config = get_config()


# =============================================================================
# Request/Response Models
# =============================================================================

class IndexRequest(BaseModel):
    """Request to index a PPTX file."""
    file_path: str
    output_dir: Optional[str] = "./data/output"


class IndexResponse(BaseModel):
    """Response for indexing request."""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    progress: float
    current_stage: Optional[str] = None
    error: Optional[str] = None


class SearchRequest(BaseModel):
    """Semantic search request."""
    query: str
    top_k: int = 5
    collection: Optional[str] = None


class SearchResult(BaseModel):
    """Search result."""
    slide_id: str
    slide_number: int
    title: str
    text: str
    score: float


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    results: List[SearchResult]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/index", response_model=IndexResponse)
async def index_pptx(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """Index a PPTX file."""
    
    # Validate file extension
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="File must be .pptx format")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = Path("./data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{job_id}_{file.filename}"
    content = await file.read()
    file_path.write_bytes(content)
    
    # Initialize job
    jobs[job_id] = {
        "status": "pending",
        "file_path": str(file_path),
        "output_dir": config.vector_store.persist_directory.replace("chroma", "output"),
        "progress": 0.0,
        "current_stage": None,
    }
    
    # Run indexing in background
    def process_file():
        try:
            worker = IndexerWorker()
            worker.process(
                input_path=str(file_path),
                output_dir=jobs[job_id]["output_dir"],
                job_id=job_id,
            )
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 1.0
        except Exception as e:
            logger.error(f"Indexing failed for job {job_id}: {e}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
    
    if background_tasks:
        background_tasks.add_task(process_file)
    else:
        process_file()
    
    return IndexResponse(
        job_id=job_id,
        status="pending",
        message=f"File uploaded. Indexing started with job ID: {job_id}",
    )


@app.get("/index/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get indexing job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0.0),
        current_stage=job.get("current_stage"),
        error=job.get("error"),
    )


@app.post("/search", response_model=SearchResponse)
async def search_presentation(request: SearchRequest):
    """Semantic search across indexed presentations."""
    
    try:
        # Initialize components
        embedder = create_llm_adapter()  # Will use sentence-transformers
        vector_store = create_vector_store(
            collection_name=request.collection or config.vector_store.collection_name,
        )
        
        # Get query embedding
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode(request.query).tolist()
        
        # Search vector store
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
        )
        
        # Format response
        search_results = []
        for r in results:
            search_results.append(SearchResult(
                slide_id=r.id,
                slide_number=r.metadata.get("slide_number", 0),
                title=r.metadata.get("title", ""),
                text=r.text,
                score=r.score,
            ))
        
        return SearchResponse(
            query=request.query,
            results=search_results,
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections")
async def list_collections():
    """List available collections."""
    try:
        vector_store = create_vector_store()
        count = vector_store.count()
        return {
            "collections": [
                {
                    "name": config.vector_store.collection_name,
                    "document_count": count,
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Metrics Endpoint
# =============================================================================

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import Counter, Gauge, generate_latest
    
    # Simple metrics
    jobs_total = Gauge("indexer_jobs_total", "Total indexing jobs")
    jobs_completed = Counter("indexer_jobs_completed", "Completed indexing jobs")
    jobs_failed = Counter("indexer_jobs_failed", "Failed indexing jobs")
    
    for job in jobs.values():
        jobs_total.inc()
        if job["status"] == "completed":
            jobs_completed.inc()
        elif job["status"] == "failed":
            jobs_failed.inc()
    
    return {"content_type": "text/plain", "body": generate_latest()}


# =============================================================================
# Main
# =============================================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
    )
