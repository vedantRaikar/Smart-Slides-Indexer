"""
Custom Plugin Development Guide
"""

# BUILDING CUSTOM PLUGINS

## Plugin Architecture Overview

All plugins inherit from abstract base classes in `pptx_indexer/plugins/base_llm.py`:

```python
from pptx_indexer.plugins import BaseLLM, BaseEmbedder, BaseVectorStore
```

Each plugin defines an interface that must be implemented.


## Example 1: Custom LLM Plugin (Claude via Anthropic)

```python
# pptx_indexer/plugins/custom_plugins/claude_llm.py

from typing import List, Dict, Any
from pptx_indexer.plugins import BaseLLM
import anthropic

class ClaudeLLM(BaseLLM):
    """Claude LLM via Anthropic API."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        """Initialize Claude client."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.temperature = 0.7
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text response."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 500),
            temperature=kwargs.get("temperature", self.temperature),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate for multiple prompts."""
        results = []
        for prompt in prompts:
            result = self.generate(prompt, **kwargs)
            results.append(result)
        return results

# Usage:
llm = ClaudeLLM(api_key="sk-ant-...")
response = llm.generate("Summarize this: ...")
```


## Example 2: Custom Embedder Plugin (E5-Large)

```python
# pptx_indexer/plugins/custom_plugins/e5_embedder.py

from typing import List
from pptx_indexer.plugins import BaseEmbedder
from transformers import AutoTokenizer, AutoModel
import torch

class E5LargeEmbedder(BaseEmbedder):
    """E5-Large embedding model (high quality)."""
    
    def __init__(self, model_name: str = "intfloat/e5-large"):
        """Initialize E5 model."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self._embedding_dim = 1024  # E5-large dimension
    
    def embed(self, text: str) -> List[float]:
        """Embed single text."""
        # E5 requires "query: " or "passage: " prefix
        if len(text) < 100:
            text = f"query: {text}"
        else:
            text = f"passage: {text}"
        
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            embedding = outputs.last_hidden_state.mean(dim=1)[0]
        
        return embedding.cpu().tolist()
    
    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts (vectorized)."""
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
        return embeddings
    
    @property
    def embedding_dim(self) -> int:
        """Embedding dimension."""
        return self._embedding_dim

# Usage:
embedder = E5LargeEmbedder()
embedding = embedder.embed("What is AI?")
```


## Example 3: Custom Vector Store (Pinecone)

```python
# pptx_indexer/plugins/custom_plugins/pinecone_store.py

from typing import List, Dict, Any, Tuple
from pptx_indexer.plugins import BaseVectorStore
import pinecone

class PineconeVectorStore(BaseVectorStore):
    """Pinecone serverless vector store."""
    
    def __init__(
        self,
        api_key: str,
        index_name: str = "slides",
        dimension: int = 1536,
    ):
        """Initialize Pinecone."""
        pinecone.init(api_key=api_key)
        
        # Create or get index
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
            )
        
        self.index = pinecone.Index(index_name)
        self.meta_storage = {}  # Simple metadata storage
    
    def add(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Add vector to store."""
        self.index.upsert(
            vectors=[(vector_id, vector, metadata or {})]
        )
        self.meta_storage[vector_id] = metadata
    
    def batch_add(
        self,
        vector_ids: List[str],
        vectors: List[List[float]],
        metadatas: List[Dict] = None,
    ) -> None:
        """Add multiple vectors."""
        vectors_to_upsert = []
        for i, vid in enumerate(vector_ids):
            meta = (metadatas[i] if metadatas else {}) or {}
            vectors_to_upsert.append((vid, vectors[i], meta))
            self.meta_storage[vid] = meta
        
        self.index.upsert(vectors=vectors_to_upsert)
    
    def search(
        self,
        vector: List[float],
        top_k: int = 5,
    ) -> List[Tuple[str, float, Dict]]:
        """Search similar vectors."""
        results = self.index.query(
            top_k=top_k,
            vector=vector,
            include_metadata=True,
        )
        
        return [
            (
                match["id"],
                match["score"],
                match["metadata"],
            )
            for match in results["matches"]
        ]
    
    def batch_search(
        self,
        vectors: List[List[float]],
        top_k: int = 5,
    ) -> List[List[Tuple[str, float, Dict]]]:
        """Search for multiple vectors."""
        return [self.search(v, top_k) for v in vectors]
    
    def delete(self, vector_id: str) -> None:
        """Delete vector."""
        self.index.delete(ids=[vector_id])
        self.meta_storage.pop(vector_id, None)
    
    def clear(self) -> None:
        """Clear all vectors."""
        self.index.delete(delete_all=True)
        self.meta_storage.clear()

# Usage:
vector_store = PineconeVectorStore(api_key="...", index_name="slides")
indexer = PPTIndexer(..., vector_store=vector_store)
```


## Example 4: Custom OCR Plugin (Google Vision)

```python
# pptx_indexer/plugins/custom_plugins/google_vision_ocr.py

from typing import List, Tuple
from pptx_indexer.plugins import BaseOCR
from google.cloud import vision

class GoogleVisionOCR(BaseOCR):
    """Google Cloud Vision OCR."""
    
    def __init__(self, project_id: str = None):
        """Initialize Vision client."""
        self.client = vision.ImageAnnotatorClient()
        self.project_id = project_id
    
    def extract_text(self, image_path: str) -> str:
        """Extract text from image."""
        with open(image_path, "rb") as f:
            image = vision.Image(content=f.read())
        
        response = self.client.text_detection(image=image)
        
        # First annotation is full text
        if response.text_annotations:
            return response.text_annotations[0].description
        
        return ""
    
    def extract_text_with_coords(
        self,
        image_path: str,
    ) -> List[Tuple[str, List[Tuple[int, int]]]]:
        """Extract text with bounding boxes."""
        with open(image_path, "rb") as f:
            image = vision.Image(content=f.read())
        
        response = self.client.text_detection(image=image)
        
        results = []
        # Skip first annotation (full text)
        for annotation in response.text_annotations[1:]:
            text = annotation.description
            vertices = annotation.bounding_poly.vertices
            coords = [(v.x, v.y) for v in vertices]
            results.append((text, coords))
        
        return results

# Usage:
ocr = GoogleVisionOCR()
text = ocr.extract_text("image.png")
```


## Example 5: Custom Image Captioner (BLIP-2)

```python
# pptx_indexer/plugins/custom_plugins/blip2_captioner.py

from typing import List
from pptx_indexer.plugins import BaseImageCaptioner
from transformers import AutoProcessor, Blip2ForConditionalGeneration
from PIL import Image

class BLIP2Captioner(BaseImageCaptioner):
    """BLIP-2 image captioning model (high quality)."""
    
    def __init__(self, device: str = "cuda"):
        """Initialize BLIP-2."""
        self.device = device
        self.processor = AutoProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            "Salesforce/blip2-opt-2.7b",
            torch_dtype=torch.float16,
            device_map=self.device,
        )
    
    def caption(self, image_path: str) -> str:
        """Generate caption for image."""
        image = Image.open(image_path).convert("RGB")
        
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        
        generated_ids = self.model.generate(**inputs, max_length=50)
        caption = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()
        
        return caption
    
    def batch_caption(self, image_paths: List[str]) -> List[str]:
        """Generate captions for multiple images."""
        return [self.caption(path) for path in image_paths]

# Usage:
captioner = BLIP2Captioner()
caption = captioner.caption("image.png")
```


## Registering Custom Plugins

```python
# Use custom plugins
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.custom_plugins import (
    ClaudeLLM,
    E5LargeEmbedder,
    PineconeVectorStore,
    GoogleVisionOCR,
    BLIP2Captioner,
)

llm = ClaudeLLM(api_key="...")
embedder = E5LargeEmbedder()
vector_store = PineconeVectorStore(api_key="...")
ocr = GoogleVisionOCR(project_id="...")
captioner = BLIP2Captioner()

indexer = PPTIndexer(
    llm=llm,
    embedder=embedder,
    vector_store=vector_store,
    ocr=ocr,
    image_captioner=captioner,
)

# Now use as normal
index = indexer.index_file("presentation.pptx")
```


## Plugin Testing Template

```python
# pptx_indexer/plugins/custom_plugins/test_custom.py

import pytest
from custom_llm import ClaudeLLM

class TestClaudeLLM:
    """Test Claude LLM plugin."""
    
    @pytest.fixture
    def llm(self):
        return ClaudeLLM(api_key="test-key")
    
    def test_generate(self, llm):
        """Test text generation."""
        response = llm.generate("Say hello")
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_batch_generate(self, llm):
        """Test batch generation."""
        prompts = ["Say hello", "Say goodbye"]
        responses = llm.batch_generate(prompts)
        assert len(responses) == 2
        assert all(isinstance(r, str) for r in responses)

# Run: pytest pptx_indexer/plugins/custom_plugins/test_custom.py
```


## Best Practices

1. **Inherit from Base Classes**: Always use provided abstract classes
2. **Implement Required Methods**: Check docstrings for all required methods
3. **Handle Errors**: Catch and re-raise meaningful exceptions
4. **Log Operations**: Use Python logging for debugging
5. **Optimize for Batching**: Implement batch_* methods for performance
6. **Test Thoroughly**: Test with real data and edge cases
7. **Document Usage**: Include docstrings with examples
8. **Version Dependencies**: Specify exact versions in requirements


## Common Issues

### "NotImplementedError: Subclasses must implement..."
- **Fix**: Make sure all required methods are implemented in your plugin

### "Plugin not found"
- **Fix**: Set environment variables or add to PluginRegistry

### Performance Issues
- **Fix**: Implement batch methods for 10x+ speedup

---

See existing plugins in `pptx_indexer/plugins/default_plugins/implementations.py` for complete examples.
