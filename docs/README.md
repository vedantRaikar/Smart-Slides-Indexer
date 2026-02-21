# Smart Slides Indexer

A production-ready system for indexing and semantic search of PowerPoint presentations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Service                          │
│  (FastAPI - Upload, Status, Search)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│   Worker 1   │           │   Worker N   │
│  (Indexing)  │           │  (Indexing)  │
└──────┬───────┘           └──────┬───────┘
       │                           │
       └─────────────┬─────────────┘
                     ▼
        ┌─────────────────────────┐
        │   Chroma Vector Store   │
        └─────────────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-org/smart-slides-indexer.git
cd smart-slides-indexer

# Install dependencies
pip install -e ".[dev]"

# Create .env file (see .env.example)
cp .env.example .env
```

### 2. Local Development

```bash
# Start services with Docker Compose
docker compose -f infra/docker-compose.yml up

# Or run directly
python -m cli.main index presentation.pptx
python -m cli.main serve
```

### 3. API Usage

```bash
# Index a presentation
curl -X POST http://localhost:8000/index \
  -F "file=@presentation.pptx"

# Check job status
curl http://localhost:8000/index/{job_id}

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "what is coupling in software", "top_k": 5}'
```

### 4. CLI Usage

```bash
# Index a PPTX file
python -m cli.main index input.pptx -o ./output

# Search
python -m cli.main search "what is coupling" -k 5

# Start API server
python -m cli.main serve --port 8000

# Show configuration
python -m cli.main info
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM__PROVIDER` | LLM provider (openai, groq, bigpickle, gemini) | groq |
| `LLM__MODEL` | Model name | llama-3.1-70b-versatile |
| `LLM__API_KEY` | API key for LLM | - |
| `EMBEDDER__MODEL` | Embedding model | all-MiniLM-L6-v2 |
| `VECTOR_STORE__PROVIDER` | Vector store (chroma, qdrant) | chroma |
| `OCR__PROVIDER` | OCR provider (paddleocr, pytesseract) | paddleocr |
| `WORKER__MAX_WORKERS` | Max parallel workers | 4 |
| `REDIS__ENABLED` | Enable Redis | false |

### API Keys

At least one API key must be set depending on provider:

- `OPENAI_API_KEY` - For OpenAI provider
- `GROQ_API_KEY` - For Groq provider (recommended for free tier)
- `GOOGLE_API_KEY` - For Gemini provider
- `ROUTEWAY_API_KEY` - For BigPickle provider

## Deployment

### Docker Compose (Local Dev)

```bash
# Build and start
docker compose -f infra/docker-compose.yml up --build

# View logs
docker compose -f infra/docker-compose.yml logs -f

# Stop
docker compose -f infra/docker-compose.yml down
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f infra/k8s-manifests.yaml

# Check status
kubectl get pods -n smart-slides
```

## Pipeline Stages

1. **Parser** - Extract slides from PPTX
2. **OCR** - Extract text from images
3. **Structure** - Analyze document structure
4. **Metadata (LLM)** - Extract keywords, summaries
5. **Embed** - Generate embeddings
6. **Graph** - Build slide relationship graph

## Development

### Running Tests

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov=workers --cov=api
```

### Code Quality

```bash
# Install pre-commit hooks
pre-commit install

# Run linting
black .
flake8 .
isort .
mypy .
```

## Data Retention & PII

- Indexed data is stored locally in `./data/`
- No PII is sent to external services without explicit configuration
- LLM API calls may process data - review provider privacy policies
- Implement data cleanup jobs for production deployments

## License

MIT License - see LICENSE file for details
