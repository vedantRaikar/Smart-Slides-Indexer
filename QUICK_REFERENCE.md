# Quick Reference Card - PPTX Indexer Framework

## Installation & Setup (1 min)

```bash
# Install
pip install -r pptx_indexer/requirements.txt

# Set API key
export OPENAI_API_KEY="sk-..."

# Verify
python -c "from pptx_indexer import PPTIndexer; print('✓ Ready')"
```

---

## Basic Usage (5 min)

### Index a Presentation
```python
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import *

indexer = PPTIndexer(
    llm=OpenAILLM(api_key="sk-..."),
    embedder=SentenceTransformerEmbedder(),
    vector_store=ChromaVectorStore(),
)

index = indexer.index_file("presentation.pptx", output_dir="./output")
print(f"✓ Indexed {len(index.slides)} slides")
```

### Query the Index
```python
from pptx_indexer.pipelines import PPTRetriever

retriever = PPTRetriever(index, indexer.embedder)

# Try different methods
results = retriever.search("query text", method="semantic", top_k=5)
results = retriever.search("query text", method="keyword", top_k=5)
results = retriever.search("query text", method="graph", top_k=5)
results = retriever.search("query text", method="hybrid", top_k=5)

for result in results:
    print(f"Slide {result.slide_id}: {result.title} (score: {result.score:.2f})")
    print(f"Content: {result.content[:200]}\n")
```

---

## Core Concepts

### SlideNode (Slide Data)
```python
slide = SlideNode(slide_number=1, title="Title")
# Fields: bullets[], images[], tables[], keywords[], topics[], summary, embeddings...
```

### SectionNode (Hierarchical Group)
```python
section = SectionNode(title="Part 1", slide_ids=[1, 2, 3])
# Fields: topic, subtopics[], keywords[], embedding...
```

### SlideGraph (Relationships)
```python
graph = slide_graph  # 8 edge types: NEXT, PREVIOUS, BELONGS_TO, SEMANTICALLY_SIMILAR, etc.
neighbors = graph.get_neighbors(slide_id, depth=2)
path = graph.get_path(start_id, end_id)
```

### DocumentIndex (Complete Index)
```python
index.document_id          # Unique ID
index.slides              # Dict[slide_id -> SlideNode]
index.sections            # Dict[section_id -> SectionNode]
index.graph               # SlideGraph
index.get_slide(slide_id) # Retrieve slide
```

---

## Retrieval Methods

### Semantic (Vector Similarity)
```python
results = retriever.search("key concept", method="semantic", top_k=5)
# Best for: General queries, topic search
```

### Keyword (Term Matching)
```python
results = retriever.search("specific term", method="keyword", top_k=5)
# Best for: Exact matches, technical terms
```

### Graph (Relationship Traversal)
```python
results = retriever.search("related concepts", method="graph", top_k=5, context_radius=2)
# Best for: Understanding connections, exploration
```

### Hybrid (Combined)
```python
results = retriever.search("anything", method="hybrid", top_k=5)
# Best for: General purpose, better recall
```

---

## Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="sk-..."
export EMBEDDING_MODEL="all-MiniLM-L6-v2"
export MAX_WORKERS="4"
```

### Runtime Config
```python
from pptx_indexer.config import IndexingConfig

config = IndexingConfig(
    llm_model="gpt-4",
    llm_temperature=0.7,
    embedding_model="all-MiniLM-L6-v2",
    embedding_batch_size=32,
    enable_ocr=True,
    enable_image_captions=True,
    max_workers=4,
)

indexer = PPTIndexer(..., config=config)
```

---

## Data Export

### To JSON
```python
index.export_index(format="json", output_path="index.json")
```

### To JSONL (streaming)
```python
index.export_index(format="jsonl", output_path="index.jsonl")
```

### To Pickle (Python native)
```python
index.export_index(format="pickle", output_path="index.pkl")
```

### To Dictionary
```python
data = index.to_dict()
index_restored = DocumentIndex.from_dict(data)
```

---

## Custom Plugins

### Use Custom LLM
```python
from pptx_indexer.plugins.custom_plugins import ClaudeLLM

llm = ClaudeLLM(api_key="sk-ant-...")
indexer = PPTIndexer(llm=llm, ...)
```

### Use Custom Embedder
```python
from pptx_indexer.plugins.custom_plugins import E5LargeEmbedder

embedder = E5LargeEmbedder()
indexer = PPTIndexer(embedder=embedder, ...)
```

### Use Custom Vector Store
```python
from pptx_indexer.plugins.custom_plugins import PineconeVectorStore

vector_store = PineconeVectorStore(api_key="...", index_name="slides")
indexer = PPTIndexer(vector_store=vector_store, ...)
```

---

## Web Integration (FastAPI)

```python
from fastapi import FastAPI
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import *
from pptx_indexer.pipelines import PPTRetriever

app = FastAPI()
indexer = PPTIndexer(...)
indices = {}

@app.post("/index")
async def index_file(file: UploadFile):
    index = indexer.index_file(file.filename)
    indices[file.filename] = index
    return {"status": "ok", "slides": len(index.slides)}

@app.post("/search")
async def search(query: str, doc: str = None, method: str = "hybrid", top_k: int = 5):
    results = []
    for name, index in (
        {doc: indices[doc]}.items() if doc else indices.items()
    ):
        retriever = PPTRetriever(index, indexer.embedder)
        results.extend(retriever.search(query, method=method, top_k=top_k))
    return [r.to_dict() for r in results[:top_k]]

# Run: uvicorn app:app --reload
```

---

## LLM/RAG Integration

```python
from pptx_indexer import PPTIndexer
from pptx_indexer.pipelines import PPTRetriever
import openai

class DocumentQA:
    def __init__(self, indexer):
        self.indexer = indexer
    
    def answer(self, query: str):
        # Retrieve context
        retriever = PPTRetriever(self.indexer.index, self.indexer.embedder)
        results = retriever.search(query, method="hybrid", top_k=3)
        context = "\n".join([r.content for r in results])
        
        # Query LLM
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Answer based on context."},
                {"role": "user", "content": f"Context:\n{context}\n\nQ:{query}"},
            ],
        )
        
        return response["choices"][0]["message"]["content"]

qa = DocumentQA(indexer)
print(qa.answer("What are the main points?"))
```

---

## Common Tasks

### Get All Keywords
```python
all_keywords = set()
for slide in index.slides.values():
    all_keywords.update(slide.keywords)
print(all_keywords)
```

### Get Slides by Keyword
```python
slides = index.get_slides_by_keyword("machine learning")
for slide in slides:
    print(f"Slide {slide.slide_number}: {slide.title}")
```

### Get Slides by Topic
```python
slides = index.get_slides_by_topic("AI")
for slide in slides:
    print(f"Slide {slide.slide_number}: {slide.title}")
```

### Get Section Slides
```python
section = index.sections["section_1"]
for slide_id in section.slide_ids:
    slide = index.slides[slide_id]
    print(f"- {slide.title}")
```

### Get Similar Slides
```python
target_slide = index.slides["slide_5"]
# Similar slides are in graph relationships
similar = graph.get_neighbors(target_slide.slide_id, edge_type="SEMANTICALLY_SIMILAR")
```

### Extract Full Text
```python
full_text = slide.get_full_text()
hierarchy = slide.get_rich_text_hierarchy()
```

---

## Debugging

### Check Index Stats
```python
print(f"Slides: {len(index.slides)}")
print(f"Sections: {len(index.sections)}")
print(f"Images: {sum(len(s.images) for s in index.slides.values())}")
print(f"Graph nodes: {len(index.graph.nodes)}")
print(f"Graph edges: {len(index.graph.edges)}")
```

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verify Embeddings
```python
print(f"Slide embeddings: {len(index.slide_embeddings)}")
print(f"Dimension: {len(list(index.slide_embeddings.values())[0])}")
```

### Check Retrieval Quality
```python
# Try different queries and methods
for method in ["semantic", "keyword", "graph", "hybrid"]:
    results = retriever.search("test", method=method, top_k=3)
    print(f"{method:10} - {results[0].score:.3f}")
```

---

## Performance Tips

### Speed Up Indexing
```python
# 1. Reduce workers
config.max_workers = 2

# 2. Disable OCR
config.enable_ocr = False

# 3. Disable image captions
config.enable_image_captions = False

# 4. Use faster LLM
indexer = PPTIndexer(llm=OpenAILLM(model="gpt-3.5-turbo"), ...)
```

### Speed Up Retrieval
```python
# 1. Reduce top_k
results = retriever.search(query, top_k=3)

# 2. Use vector store (faster than manual)
vector_store = ChromaVectorStore()  # Not None

# 3. Cache embeddings
embedder._cache = {}
```

### Reduce Memory
```python
# 1. Use smaller embeddings
embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")  # Small

# 2. Don't store all embeddings
config.export_embeddings = False

# 3. Use external vector store (don't keep in memory)
```

---

## File Locations

| Component | File |
|-----------|------|
| Main indexer | `pptx_indexer/pipelines/indexing_pipeline.py` |
| Main retriever | `pptx_indexer/pipelines/retrieval_pipeline.py` |
| Data models | `pptx_indexer/schemas/` |
| Plugins | `pptx_indexer/plugins/` |
| Examples | `pptx_indexer/examples/` |
| Tests | `pptx_indexer/tests/` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Module not found" | `pip install -r pptx_indexer/requirements.txt` |
| "OPENAI_API_KEY not found" | `export OPENAI_API_KEY="sk-..."` |
| Low retrieval quality | Use `method="hybrid"`, increase `top_k`, try different embedder |
| Slow indexing | Reduce workers, disable OCR, use faster LLM |
| Out of memory | Use smaller embeddings, external vector store |
| No results | Check query terms, try keyword method, verify index contents |

---

## Resources

- **Main Guide**: `README_PPTX_INDEXER.md`
- **Architecture**: `ARCHITECTURE.md`
- **Deployment**: `DEPLOYMENT.md`
- **Plugins**: `CUSTOM_PLUGINS.md`
- **Integration**: `INTEGRATION_GUIDE.md`
- **Examples**: `pptx_indexer/examples/`
- **Tests**: `pptx_indexer/tests/`

---

**Version**: 1.0 | **Status**: Production Ready | Last Updated: 2024
