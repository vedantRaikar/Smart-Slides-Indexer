"# Smart Slides Indexer - AutoML GenAI Service

An intelligent AutoML service for Generative AI that automatically optimizes and manages LLM pipelines. It provides auto-tuning of prompts, intelligent model routing, performance monitoring, and multi-provider LLM support.

## Features

✨ **Core Features:**
- **Multi-Provider Support**: OpenAI (GPT-4, GPT-3.5), Anthropic (Claude), Google Generative AI
- **Auto Prompt Optimization**: Multiple strategies (iterative, chain-of-thought, few-shot)
- **Intelligent Model Routing**: Random, round-robin, or cost-optimized routing
- **Pipeline Orchestration**: Chain multiple models and prompts
- **Performance Monitoring**: Track latency, cost, and accuracy
- **Result Caching**: Automatic caching of results for repeated prompts
- **Batch Processing**: Process multiple prompts in parallel
- **Persistent Storage**: SQLite/PostgreSQL for configuration and execution history

## Architecture

```
┌─────────────────────────────────────────────────────┐
│             AutoML GenAI Service                    │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Pipeline Mgr │  │  Optimizer   │  │  Storage   │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
├─────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│  │  OpenAI    │ │ Anthropic  │ │  Google    │      │
│  │  Models    │ │  Models    │ │  Models    │      │
│  └────────────┘ └────────────┘ └────────────┘      │
└─────────────────────────────────────────────────────┘
```

## Installation

1. **Clone and setup:**
```bash
cd Smart-Slides-Indexer
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix/MacOS
```

2. **Install dependencies:**
```bash
pip install -e ".[dev]"
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Quick Start

### Basic Pipeline

```python
import asyncio
from app.service import AutoMLGenAIService

async def main():
    service = AutoMLGenAIService()
    
    # Create a pipeline
    pipeline_id = service.create_pipeline(
        name="my-pipeline",
        models=[
            {
                "name": "gpt-4",
                "provider": "openai",
                "model_id": "gpt-4-turbo-preview",
                "custom_params": {"api_key": "your-key"},
            }
        ]
    )
    
    # Execute a prompt
    result = await service.execute(
        pipeline_id=pipeline_id,
        prompt="Write a summary about AI"
    )
    
    print(f"Output: {result.output}")
    print(f"Latency: {result.latency:.2f}s")
    
    service.close()

asyncio.run(main())
```

### Prompt Optimization

```python
service = AutoMLGenAIService()

# Auto-optimize a prompt
optimized = service.optimize_prompt(
    prompt="Write about AI",
    strategy="chain_of_thought"  # iterative, few_shot
)
```

### Batch Processing

```python
results = await service.batch_execute(
    pipeline_id=pipeline_id,
    prompts=[
        "Summarize quantum computing",
        "Explain blockchain",
        "Describe ML",
    ],
    parallel=True
)
```

## API Server

Run the FastAPI server:

```bash
python -m uvicorn app.api:app --reload
```

### API Endpoints

**Create Pipeline:**
```bash
POST /pipelines
{
    "name": "content-gen",
    "models": [
        {
            "name": "gpt-4",
            "provider": "openai",
            "model_id": "gpt-4-turbo-preview"
        }
    ]
}
```

**Execute Prompt:**
```bash
POST /pipelines/{pipeline_id}/execute
{
    "prompt": "Write a summary about AI",
    "model_name": "gpt-4"
}
```

**Batch Execute:**
```bash
POST /pipelines/{pipeline_id}/batch-execute
{
    "prompts": ["Prompt 1", "Prompt 2"],
    "parallel": true
}
```

**Get Metrics:**
```bash
GET /pipelines/{pipeline_id}/metrics
```

**Optimize Prompt:**
```bash
POST /optimize-prompt
{
    "prompt": "Write about AI",
    "strategy": "chain_of_thought"
}
```

## Configuration

### Model Configuration

```python
ModelConfig(
    name="gpt-4",
    provider=ModelProvider.OPENAI,
    model_id="gpt-4-turbo-preview",
    temperature=0.7,          # 0.0-2.0
    max_tokens=2048,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    timeout=30,
    retry_count=3,
    custom_params={}
)
```

### Pipeline Configuration

```python
PipelineConfig(
    name="my-pipeline",
    models=[...],
    prompts=[...],
    use_routing=True,
    routing_strategy="round_robin",  # random, cost_optimized
    cache_results=True,
    log_results=True,
)
```

## Performance Monitoring

```python
# Get metrics
metrics = service.get_pipeline_metrics(pipeline_id)
# {
#     "total_executions": 10,
#     "successful_executions": 10,
#     "average_latency": 2.5,
#     "cache_size": 5
# }

# Get execution history
history = service.get_execution_history(pipeline_id)

# Get performance stats
stats = service.get_performance_stats(pipeline_id)
# {
#     "total_executions": 10,
#     "average_latency": 2.5,
#     "total_cost": 0.15
# }
```

## Project Structure

```
Smart-Slides-Indexer/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main entry point & examples
│   ├── api.py               # FastAPI REST endpoints
│   ├── config.py            # Configuration management
│   ├── models.py            # LLM model wrappers
│   ├── optimizer.py         # Prompt optimization engine
│   ├── pipeline.py          # Pipeline orchestration
│   ├── service.py           # Core service
│   └── storage.py           # Persistent storage
├── pyproject.toml           # Project configuration
├── .env.example             # Environment template
└── README.md                # This file
```

## Use Cases

### 1. Content Generation Pipeline
```python
# Create pipeline for blog writing
pipeline = service.create_pipeline(
    name="content-gen",
    models=[
        {"name": "gpt-4", "provider": "openai", ...},
        {"name": "claude", "provider": "anthropic", ...}
    ],
    routing_strategy="cost_optimized"
)

# Auto-optimize prompts and generate content
optimized = service.optimize_prompt(base_prompt, "chain_of_thought")
result = await service.execute(pipeline, optimized)
```

### 2. Multi-Model Comparison
```python
# Compare outputs from different models
prompts = [prompt1, prompt2, prompt3]
results = await service.batch_execute(pipeline, prompts)

# Track performance metrics
metrics = service.get_pipeline_metrics(pipeline)
```

### 3. Cost Optimization
```python
# Route to cheaper models while maintaining quality
pipeline = service.create_pipeline(
    name="cost-optimized",
    routing_strategy="cost_optimized"  # Automatically selects cheaper models
)
```

## Advanced Features

### Custom Prompt Strategies
- **Iterative**: Automatically improve prompt structure
- **Chain-of-Thought**: Add step-by-step reasoning
- **Few-Shot**: Include relevant examples

### Monitoring & Analytics
- Track latency per model
- Monitor cost trends
- Cache hit rates
- Error tracking

### Scalability
- Async/await support for concurrent requests
- Batch processing for efficiency
- Connection pooling for databases
- Rate limiting ready

## Environment Variables

```
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
DATABASE_URL=sqlite:///automl.db
DEBUG=false
LOG_LEVEL=INFO
```

## Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app
```

## Roadmap

- [ ] Add Redis caching backend
- [ ] Model fine-tuning support
- [ ] Advanced analytics dashboard
- [ ] WebSocket support for streaming
- [ ] Multi-language support
- [ ] Custom model providers
- [ ] Cost estimation module
- [ ] A/B testing framework

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- 📧 Email: support@example.com
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
" 
