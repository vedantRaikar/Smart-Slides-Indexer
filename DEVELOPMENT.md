"""
Implementation Guide for AutoML GenAI Service
"""

# Development Guide

## How to Build & Extend

### 1. Adding a New Model Provider

To add support for a new LLM provider:

```python
# In app/models.py

from .config import ModelConfig, ModelProvider

class MyCustomLLMModel(BaseLLMModel):
    """My custom LLM provider wrapper."""
    
    def _initialize_client(self):
        # Initialize your LLM client
        from my_llm_package import LLMClient
        self.client = LLMClient(api_key=self.config.custom_params.get("api_key"))
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # Implement generation
        response = await self.client.generate(prompt)
        return response.text
    
    async def stream_generate(self, prompt: str, **kwargs):
        # Implement streaming
        async for chunk in self.client.stream(prompt):
            yield chunk


# Register in ModelFactory
ModelFactory.register(ModelProvider.CUSTOM, MyCustomLLMModel)
```

### 2. Custom Prompt Optimization Strategies

Add new optimization strategies:

```python
# In app/optimizer.py

def _optimize_custom_strategy(self, prompt: str) -> str:
    '''Your custom optimization logic'''
    # Implement your strategy
    return optimized_prompt

# Then use it
optimized = optimizer.optimize_prompt(prompt, "custom_strategy")
```

### 3. Adding Performance Metrics

Track custom metrics:

```python
# In app/pipeline.py

@dataclass
class ExecutionResult:
    # Add your custom fields
    custom_score: float = 0.0
    user_rating: int = 0
    tags: list[str] = field(default_factory=list)
```

### 4. Database Schema Extension

Add new tables for custom data:

```python
# In app/storage.py

class CustomDataRecord(Base):
    __tablename__ = "custom_data"
    
    id = Column(String, primary_key=True)
    pipeline_id = Column(String)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
```

## Performance Optimization Tips

### 1. Caching Strategy
```python
# Enable caching for frequently used prompts
pipeline = service.create_pipeline(
    name="cached-pipeline",
    models=[...],
    cache_results=True  # Store results for identical prompts
)
```

### 2. Parallel Execution
```python
# Process prompts in parallel for better throughput
results = await service.batch_execute(
    pipeline_id,
    prompts=[...],
    parallel=True  # Uses asyncio for concurrency
)
```

### 3. Model Selection Strategy
```python
# Use cost-optimized routing for budget-conscious deployments
pipeline = service.create_pipeline(
    name="cost-optimized",
    routing_strategy="cost_optimized"  # Routes to cheaper models
)

# Use round-robin for balanced load
pipeline = service.create_pipeline(
    name="balanced",
    routing_strategy="round_robin"  # Distributes load evenly
)
```

### 4. Database Indexing
```python
# Add indexes for frequently queried fields
from sqlalchemy import Index

# Add this to your database models
__table_args__ = (
    Index('idx_pipeline_timestamp', 'pipeline_id', 'timestamp'),
    Index('idx_model_latency', 'model_used', 'latency'),
)
```

## Deployment Scenarios

### 1. Standalone Service

```bash
python -m app.main
```

### 2. REST API Server

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000
```

### 3. Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -e .

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: automl-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: automl-service
  template:
    metadata:
      labels:
        app: automl-service
    spec:
      containers:
      - name: automl-service
        image: automl-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-key
```

## Monitoring & Observability

### Key Metrics to Track

```python
metrics = {
    "pipeline.executions.total": counter,
    "pipeline.executions.success": counter,
    "pipeline.executions.failures": counter,
    "pipeline.execution.latency": histogram,
    "pipeline.cache.hits": counter,
    "pipeline.cache.misses": counter,
    "models.cost.total": gauge,
    "models.usage.by_provider": gauge,
}
```

### Logging Configuration

```python
from loguru import logger

# Add file logging
logger.add("logs/automl.log", rotation="500 MB")

# Add structured logging
logger.add(
    lambda msg: send_to_datadog(msg),
    format="{message}"
)
```

## Security Best Practices

1. **API Key Management**
   - Never hardcode API keys
   - Use environment variables
   - Rotate keys regularly

2. **Input Validation**
   - Validate all user inputs
   - Sanitize prompts
   - Limit prompt length

3. **Rate Limiting**
   - Implement per-user limits
   - Prevent API abuse
   - Use exponential backoff

4. **Encryption**
   - Encrypt sensitive data in database
   - Use HTTPS only
   - Secure database connections

## Testing Strategy

### Unit Tests
```python
import pytest
from app.service import AutoMLGenAIService

@pytest.mark.asyncio
async def test_pipeline_creation():
    service = AutoMLGenAIService()
    pipeline_id = service.create_pipeline(
        name="test",
        models=[...]
    )
    assert pipeline_id is not None
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_end_to_end_execution():
    service = AutoMLGenAIService()
    pipeline_id = service.create_pipeline(...)
    result = await service.execute(pipeline_id, "test prompt")
    assert result.success
    assert len(result.output) > 0
```

### Load Testing
```bash
# Using locust
locust -f locustfile.py --host=http://localhost:8000
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Check .env file exists
   - Verify API key validity
   - Check API key permissions

2. **Model Loading Failures**
   - Ensure dependencies installed
   - Check provider configuration
   - Verify API credentials

3. **Performance Issues**
   - Enable caching
   - Use batch processing
   - Check database indexes
   - Monitor API rate limits

4. **Database Errors**
   - Verify database URL
   - Check database permissions
   - Run migrations
   - Check storage space

## Future Enhancements

1. **Model Fine-tuning**
   - Add support for custom model training
   - Track fine-tuning metrics
   - Store fine-tuned models

2. **Advanced Analytics**
   - Real-time dashboard
   - Cost analysis tool
   - Performance comparison

3. **AutoML Features**
   - Automatic hyperparameter tuning
   - Network architecture search
   - Ensemble methods

4. **Multi-Modal Support**
   - Image generation models
   - Audio processing
   - Multimodal combinations

## References

- [LangChain Docs](https://python.langchain.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
