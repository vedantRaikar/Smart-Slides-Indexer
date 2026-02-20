"""
Deployment & Integration Guide for PPTX Indexer
"""

# QUICK START

## Installation

```bash
# Clone or navigate to project
cd Smart-Slides-Indexer

# Install dependencies
pip install -r pptx_indexer/requirements.txt

# Set API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify installation
python -c "import pptx_indexer; print('✓ Framework installed')"
```


## 5-Minute Example

```python
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import (
    OpenAILLM,
    SentenceTransformerEmbedder,
    ChromaVectorStore,
    PytesseractOCR,
)

# Initialize plugins
llm = OpenAILLM("gpt-4", api_key="sk-...")
embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
vector_store = ChromaVectorStore()
ocr = PytesseractOCR()

# Create indexer
indexer = PPTIndexer(
    llm=llm,
    embedder=embedder,
    vector_store=vector_store,
    ocr=ocr,
)

# Index PowerPoint
index = indexer.index_file(
    "presentation.pptx",
    output_dir="./indexed_output"
)

# Query Retrieved
from pptx_indexer.pipelines import PPTRetriever

retriever = PPTRetriever(index, embedder)

# Run queries
results = retriever.search(
    "What are the main topics?",
    method="hybrid",
    top_k=5
)

for result in results:
    print(f"Slide {result.slide_id}: {result.title}")
    print(f"Score: {result.score:.3f}")
    print(f"Content:\n{result.content}\n")
```


# PRODUCTION DEPLOYMENT

## Architecture Patterns

### Pattern 1: Web Service (FastAPI)

```python
# app.py
from fastapi import FastAPI, File, UploadFile
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import *

app = FastAPI()

# Initialize indexer once
indexer = PPTIndexer(
    llm=OpenAILLM(model="gpt-4"),
    embedder=SentenceTransformerEmbedder(),
    vector_store=ChromaVectorStore(),
)

@app.post("/index")
async def index_presentation(file: UploadFile):
    """Index uploaded PowerPoint."""
    with open(file.filename, "wb") as f:
        f.write(file.file.read())
    
    index = indexer.index_file(file.filename)
    return {"document_id": index.document_id, "slides": len(index.slides)}

@app.post("/search")
async def search(document_id: str, query: str, method: str = "hybrid"):
    """Search indexed presentation."""
    # Load index from storage
    index = load_index_from_db(document_id)
    
    retriever = PPTRetriever(index, indexer.embedder)
    results = retriever.search(query, method=method, top_k=5)
    
    return [r.to_dict() for r in results]

# Run: uvicorn app:app --reload
```

### Pattern 2: Batch Processing (Celery)

```python
# tasks.py
from celery import Celery
from pptx_indexer import PPTIndexer

celery_app = Celery("tasks")

indexer = PPTIndexer(
    llm=OpenAILLM(model="gpt-3.5-turbo"),
    embedder=SentenceTransformerEmbedder("all-MiniLM-L6-v2"),
    vector_store=ChromaVectorStore(),
)

@celery_app.task
def index_presentation_async(file_path: str):
    """Index presentation in background."""
    try:
        index = indexer.index_file(file_path)
        
        # Save to database
        store_index_in_db(index)
        
        return {"status": "success", "doc_id": index.document_id}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# Trigger: index_presentation_async.delay("path/to/file.pptx")
```

### Pattern 3: Vector Database Integration

```python
# Using Chroma with persistence
from chromadb.config import Settings
from pptx_indexer.plugins.default_plugins import ChromaVectorStore

# Persistent Chroma
settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data",
    anonymized_telemetry=False,
)

vector_store = ChromaVectorStore(settings=settings)

# Now vectors persist across runs
indexer = PPTIndexer(..., vector_store=vector_store)
index = indexer.index_file("ppt.pptx")

# Later, vectors remain available
```

### Pattern 4: LLM RAG Integration

```python
# Use indexed presentations in RAG

from pptx_indexer import PPTIndexer
from pptx_indexer.pipelines import PPTRetriever
import openai

# Index presentations
indexer = PPTIndexer(...)
indexes = []
for ppt_file in list_ppt_files():
    index = indexer.index_file(ppt_file)
    indexes.append(index)

# For queries, retriever context
def rag_query(user_question: str):
    # 1. Retrieve relevant slides
    combined_results = []
    for index in indexes:
        retriever = PPTRetriever(index, indexer.embedder)
        results = retriever.search(user_question, top_k=3)
        combined_results.extend(results)
    
    # 2. Build context
    context = "\n\n".join([
        f"Slide {r.slide_id}: {r.content}"
        for r in combined_results[:5]  # Top 5
    ])
    
    # 3. Query LLM
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_question}"},
        ],
    )
    
    return response["choices"][0]["message"]["content"]

answer = rag_query("What is the focus of section 2?")
```


## Configuration Management

### Environment Variables

```bash
# LLM
export OPENAI_API_KEY="xxx"
export OPENAI_MODEL="gpt-4"
export OPENAI_TEMPERATURE="0.7"

# Embeddings
export EMBEDDING_MODEL="all-MiniLM-L6-v2"
export EMBEDDING_BATCH_SIZE="32"

# Storage
export VECTOR_STORE_TYPE="chroma"
export CHROMA_PERSIST_DIR="./data/chroma"

# OCR
export OCR_LANGUAGES="eng,french"
export OCR_ENABLED="true"

# Processing
export MAX_WORKERS="4"
export TIMEOUT_SECONDS="300"
```

### Config File (config.yaml)

```yaml
indexing:
  llm:
    provider: openai
    model: gpt-4
    temperature: 0.7
    max_tokens: 500
  
  embeddings:
    model: all-MiniLM-L6-v2
    batch_size: 32
  
  ocr:
    enabled: true
    languages:
      - eng
      - fra
  
  processing:
    max_workers: 4
    timeout_seconds: 300
    extract_images: true
    extract_tables: true

retrieval:
  top_k: 5
  methods:
    - semantic
    - keyword
    - graph
    - hybrid
  
  graph_expansion:
    enabled: true
    context_radius: 2
```

### Load Config

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class IndexingSettings(BaseSettings):
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = IndexingSettings()

# Usage
llm = OpenAILLM(api_key=settings.openai_api_key, model=settings.openai_model)
```


## Data Persistence

### Option 1: JSON Export

```python
# Export to JSON
index.export_index(format="json", output_path="./index.json")

# Later: Load
import json
with open("index.json") as f:
    index_dict = json.load(f)
    index = DocumentIndex.from_dict(index_dict)
```

### Option 2: Pickle

```python
# Export to pickle
index.export_index(format="pickle", output_path="./index.pkl")

# Later: Load
import pickle
with open("index.pkl", "rb") as f:
    index = pickle.load(f)
```

### Option 3: Database (PostgreSQL + pgvector)

```python
# Setup (requires pgvector extension)
import psycopg2
from pgvector.psycopg2 import register_vector

conn = psycopg2.connect(...)
register_vector(conn)

# Store
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO presentations (id, name, data) VALUES (%s, %s, %s)",
    (index.document_id, index.title, json.dumps(index.to_dict()))
)

# Store embeddings
for slide_id, embedding in index.slide_embeddings.items():
    cursor.execute(
        "INSERT INTO slide_embeddings (slide_id, embedding) VALUES (%s, %s)",
        (slide_id, embedding)  # pgvector handles serialization
    )

conn.commit()
```


## Monitoring & Observability

### Logging

```python
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("indexer.log"),
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

# Usage already in code
# PPTIndexer logs:
# - Parse: "Parsing slide 1/10..."
# - Structure: "Detected 3 sections"
# - Graph: "Built graph with 20 nodes"
# - Metadata: "Extracted metadata for slide 5"
# - Index: "Generated embeddings for 10 slides"
```

### Metrics

```python
import time
from dataclasses import dataclass

@dataclass
class IndexingMetrics:
    total_time: float
    parse_time: float
    analyze_time: float
    graph_time: float
    metadata_time: float
    index_time: float
    total_slides: int
    total_tokens_used: int
    total_embeddings_generated: int

# Collect
metrics = IndexingMetrics(...)

# Report
print(f"Indexed {metrics.total_slides} slides in {metrics.total_time:.2f}s")
print(f"Tokens used: {metrics.total_tokens_used}")
print(f"Cost: ${metrics.total_tokens_used * 0.00002:.2f}")  # ~$0.00002 per token
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    """Check system status."""
    return {
        "status": "healthy",
        "vector_store": vector_store.health_check(),
        "llm": llm.health_check(),
        "embedder": embedder.health_check(),
    }
```


## Performance Tuning

### Batch Processing

```python
# Index multiple files efficiently
from concurrent.futures import ThreadPoolExecutor

files = ["ppt1.pptx", "ppt2.pptx", "ppt3.pptx"]
indexes = []

def index_file(file_path):
    return indexer.index_file(file_path)

with ThreadPoolExecutor(max_workers=4) as executor:
    indexes = list(executor.map(index_file, files))
```

### Caching

```python
from functools import lru_cache

class PPTRetrieverCached(PPTRetriever):
    @lru_cache(maxsize=1000)
    def _cosine_similarity(self, vec1, vec2):
        """Cache similarity computations."""
        return super()._cosine_similarity(vec1, vec2)
```

### Vectorization

```python
# Use NumPy for faster similarity
import numpy as np

# Instead of loop
similarities = []
for slide_embedding in slide_embeddings:
    sim = cosine_similarity(query_embedding, slide_embedding)
    similarities.append(sim)

# Use vectorized
query_embedding = np.array(query_embedding)
slide_embeddings = np.array(list(slide_embeddings))
similarities = np.dot(slide_embeddings, query_embedding)  # Much faster
```


## Error Handling & Recovery

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def index_with_retry(file_path):
    """Index with automatic retry."""
    return indexer.index_file(file_path)

# Try-catch patterns already in code:
# - try/except in each pipeline stage
# - Fallback behaviors (e.g., manual similarity if vector store fails)
# - Graceful degradation (OCR optional, etc)
```


## Security Best Practices

1. **API Keys**: Use environment variables or secrets manager
   ```python
   import os
   api_key = os.getenv("OPENAI_API_KEY")  # Never hardcode
   ```

2. **Rate Limiting**: Implement on API endpoints
   ```python
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/search")
   @limiter.limit("100/minute")
   async def search(...):
       ...
   ```

3. **Input Validation**: Validate file types and sizes
   ```python
   ALLOWED_EXTENSIONS = {".pptx", ".ppt"}
   MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
   
   def validate_file(file_path):
       if not file_path.suffix in ALLOWED_EXTENSIONS:
           raise ValueError("Invalid file type")
       if os.path.getsize(file_path) > MAX_FILE_SIZE:
           raise ValueError("File too large")
   ```

4. **Data Privacy**: Encrypt data at rest
   ```python
   from cryptography.fernet import Fernet
   
   cipher = Fernet(encryption_key)
   encrypted_data = cipher.encrypt(embeddings_bytes)
   ```

5. **Audit Logging**: Log all queries and indexing
   ```python
   logger.info(f"Indexed presentation: {file_path} by user: {user_id}")
   logger.info(f"Query: '{query}' by user: {user_id} - returned {len(results)} results")
   ```


# TROUBLESHOOTING

## Common Issues

### "Module not found" errors
- **Fix**: Install dependencies: `pip install -r pptx_indexer/requirements.txt`

### "OPENAI_API_KEY not found"
- **Fix**: `export OPENAI_API_KEY="sk-..."`

### Low retrieval quality
- **Try**: 
  - Increase `top_k` in search
  - Use `method="hybrid"` instead of `"semantic"`
  - Check embeddings model (try `all-mpnet-base-v2` for better quality)

### Slow indexing
- **Try**:
  - Reduce `max_workers`
  - Disable OCR: `ocr=None`
  - Use smaller embeddings model

### Running out of memory
- **Try**:
  - Reduce `embedding_batch_size`
  - Process files one at a time
  - Use external vector store (Pinecone) instead of Chroma in-memory


---

For more details, see README_PPTX_INDEXER.md and code comments.
