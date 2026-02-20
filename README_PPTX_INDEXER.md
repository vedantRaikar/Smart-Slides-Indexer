# 🚀 PPTX Indexer - Intelligent Slide Indexing Framework

A **production-grade, extensible framework for converting PowerPoint presentations into semantic, hierarchical, graph-based indices** that can be used by LLMs and RAG systems instead of naive text chunking.

## ✨ Why PPTX Indexer?

### The Problem with Naive Chunking
❌ Loses hierarchical structure  
❌ Breaks content semantic meaning  
❌ Ignores visual-text relationships  
❌ Doesn't preserve pedagogical flow  
❌ Creates orphaned fragments  

### The PPTX Indexer Solution
✅ **Preserves hierarchy** - sections, subsections, slides  
✅ **Semantic understanding** - LLM-extracted topics and concepts  
✅ **Graph-based representation** - relationships and traversal  
✅ **Multi-resolution indexing** - slide, section, and document level  
✅ **Image intelligence** - OCR + captions + embeddings  
✅ **LLM-ready output** - structured, queryable indices  

## 🎯 Core Architecture

```
PowerPoint File
    ↓
[PARSE] Extract structural content (titles, bullets, images, tables)
    ↓
[ANALYZE] Detect sections, hierarchy, topics
    ↓
[GRAPH] Build hierarchical + semantic relationship graph
    ↓
[METADATA] LLM extracts keywords, topics, summaries
    ↓
[INDEX] Embeddings + vector store + graph persistence
    ↓
DocumentIndex (Ready for LLM/RAG)
```

## 🏗️ Project Structure

```
pptx_indexer/
│
├── core/                        # Core indexing logic
│   ├── parser.py               # PPT parsing & content extraction
│   ├── structure_analyzer.py   # Hierarchy & topic detection
│   ├── slide_graph.py          # Graph construction
│   ├── metadata_extractor.py   # LLM-powered metadata
│   ├── index_builder.py        # Index assembly & export
│   └── utils.py                # Utilities
│
├── plugins/                     # Pluggable components
│   ├── base_llm.py             # Abstract base classes
│   └── default_plugins/        # Ready-to-use implementations
│       ├── implementations.py  # OpenAI, Embedders, Vector Stores
│       └── __init__.py
│
├── pipelines/                   # High-level workflows
│   ├── indexing_pipeline.py    # Complete indexing (the main entry point)
│   └── retrieval_pipeline.py   # Query & retrieval
│
├── schemas/                     # Data models
│   ├── slide_node.py           # Core slide representation
│   ├── slide_graph_schema.py   # Graph structure
│   └── document_index.py       # Complete index
│
├── examples/                    # Usage examples
│   ├── index_ppt.py            # Index a presentation
│   └── query_ppt.py            # Query an index
│
├── config.py                    # Global configuration
└── __init__.py                  # Package initialization
```

## ⚡ Quick Start

### 1. Installation

```bash
pip install pptx-indexer

# Or with optional dependencies
pip install pptx-indexer[llm,embeddings,vectorstore,ocr]
```

### 2. Basic Usage

```python
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import (
    OpenAILLM,
    SentenceTransformerEmbedder,
    ChromaVectorStore,
)

# Initialize plugins
llm = OpenAILLM(api_key="sk-...")
embedder = SentenceTransformerEmbedder()
vector_store = ChromaVectorStore()

# Create indexer
indexer = PPTIndexer(
    llm=llm,
    embedder=embedder,
    vector_store=vector_store,
)

# Index your presentation
index = indexer.index_file("presentation.pptx", output_dir="./output")
```

### 3. Query the Index

```python
from pptx_indexer import PPTRetriever

# Create retriever
retriever = PPTRetriever(
    index=index,
    embedder=embedder,
)

# Semantic search
results = retriever.search(
    query="What are neural networks?",
    top_k=5,
    method="semantic",  # semantic, keyword, graph, or hybrid
)

for result in results:
    print(f"{result.slide_title}: {result.score:.2f}")
```

## 🔧 Core Concepts

### 1. SlideNode - Atomic Indexing Unit
```python
@dataclass
class SlideNode:
    slide_id: str
    title: str
    bullets: List[BulletPoint]  # Hierarchical bullets
    images: List[ImageNode]
    tables: List[TableNode]
    
    # Metadata (LLM-extracted)
    keywords: List[str]
    topics: List[str]
    summary: str
    learning_objectives: List[str]
    
    # Embeddings
    embedding: List[float]
    title_embedding: List[float]
    
    # Relationships
    next_slide_id: Optional[str]
    prev_slide_id: Optional[str]
    references: List[str]
```

### 2. SectionNode - Hierarchical Grouping
```python
@dataclass
class SectionNode:
    section_id: str
    title: str
    slide_ids: List[str]  # Slides in this section
    topic: str
    subtopics: List[str]
    embedding: List[float]
```

### 3. SlideGraph - Semantic Relationships
```
Types of edges:
├── NEXT/PREVIOUS          (Sequential ordering)
├── BELONGS_TO/CONTAINS    (Hierarchical)
├── SEMANTICALLY_SIMILAR   (Semantic closeness)
├── REFERENCES             (Cross-references)
├── EXPANDS/SUMMARIZES     (Detailed vs summary)
└── RELATED                (General relationship)
```

### 4. DocumentIndex - Complete Index
```python
@dataclass
class DocumentIndex:
    slides: Dict[str, SlideNode]
    sections: Dict[str, SectionNode]
    graph: SlideGraph
    
    # Multi-resolution embeddings
    slide_embeddings: Dict[str, List[float]]
    section_embeddings: Dict[str, List[float]]
    document_embedding: List[float]
    
    # Search indices
    keyword_to_slides: Dict[str, List[str]]
    topic_to_slides: Dict[str, List[str]]
    concept_clusters: Dict[int, List[str]]
    
    # Statistics
    stats: DocumentStats
```

## 🔌 Plugin System

### Using Default Plugins

```python
from pptx_indexer.plugins.default_plugins import (
    OpenAILLM,                    # OpenAI GPT
    SentenceTransformerEmbedder,  # HuggingFace embeddings
    ChromaVectorStore,             # Vector database
    PytesseractOCR,               # Image text extraction
)
```

### Creating Custom Plugins

```python
from pptx_indexer.plugins.base_llm import BaseLLM

class MyCustomLLM(BaseLLM):
    def generate(self, prompt: str, **kwargs) -> str:
        # Your implementation
        pass
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        # Your implementation
        pass

# Use in indexer
indexer = PPTIndexer(
    llm=MyCustomLLM(),
    embedder=embedder,
)
```

### Available Base Classes

```python
# LLM plugins
from pptx_indexer.plugins.base_llm import BaseLLM

# Embedding plugins
from pptx_indexer.plugins.base_llm import BaseEmbedder

# Vector store plugins
from pptx_indexer.plugins.base_llm import BaseVectorStore

# OCR plugins
from pptx_indexer.plugins.base_llm import BaseOCR

# Image captioning plugins
from pptx_indexer.plugins.base_llm import BaseImageCaptioner

# Graph database plugins
from pptx_indexer.plugins.base_llm import BaseGraphDB
```

## 🎯 Retrieval Modes

### Semantic Search
Uses vector embeddings for fast similarity matching.
```python
results = retriever.search(query, method="semantic")
```

### Keyword Search
Pattern matching across slide content.
```python
results = retriever.search(query, method="keyword")
```

### Graph-Based Search
Traverses relationships to find contextually related slides.
```python
results = retriever.search(query, method="graph")
```

### Hybrid Search
Combines multiple methods with weighted scoring.
```python
results = retriever.search(query, method="hybrid")
```

## 📊 Multi-Resolution Indexing

The framework creates indices at three levels:

```
Document Level
└── Document Embedding (mean of all slides)

Section Level
└── Section Embedding (for each group of slides)

Slide Level
├── Full Slide Embedding
├── Title Embedding
└── Content Embedding
```

This enables retrieval at any granularity level.

## 🚀 Advanced Features

### 1. Concept Clustering
Automatically groups semantically similar slides
```python
clusters = graph_builder.detect_concepts(graph)
for cluster_id, slide_ids in clusters.items():
    print(f"Concept {cluster_id}: {slide_ids}")
```

### 2. Cross-Slide Linking
Identifies and maintains relationships
```python
context = retriever.get_context(slide_id, context_radius=2)
# Returns: target slide + related + section
```

### 3. Importance Scoring
Ranks slides by graph centrality
```python
scores = graph_builder.compute_importance_scores(graph)
```

### 4. Rich Context Extraction
```python
context = retriever.get_context(
    slide_id="slide_123",
    context_radius=2,  # Include neighbors
)
# Includes: target + previous/next + related
```

## 📈 Export Formats

Export your index in multiple formats:

```python
# JSON (full index)
indexer.export_index(index, "index.json", format="json")

# JSONL (line-delimited, for streaming)
indexer.export_index(index, "index.jsonl", format="jsonl")

# Pickle (Python binary)
indexer.export_index(index, "index.pkl", format="pickle")

# Graph structure
indexer.export_graph(graph, "graph.json")
```

## ⚙️ Configuration

```python
from pptx_indexer.config import IndexingConfig

config = IndexingConfig(
    # LLM
    llm_model="gpt-3.5-turbo",
    llm_temperature=0.3,
    
    # Embeddings
    embedding_model="all-MiniLM-L6-v2",
    
    # OCR
    enable_ocr=True,
    
    # Image captions
    enable_image_captions=True,
    
    # Advanced
    compute_similarity_matrix=True,
    cluster_concepts=True,
    generate_summaries=True,
)

indexer = PPTIndexer(..., config=config)
```

## 🎓 Examples

### Example 1: Index a Presentation
```bash
cd pptx_indexer/examples
python index_ppt.py
```

This will:
- Parse your presentation
- Extract metadata
- Build the graph
- Generate embeddings
- Export all outputs

### Example 2: Query an Index
```bash
python query_ppt.py
```

Demonstrates retrieval modes and context extraction.

## 🧪 Testing

```bash
pytest tests/ -v
pytest tests/ --cov=pptx_indexer
```

## 📚 API Reference

### PPTIndexer
Main entry point for indexing.

```python
indexer = PPTIndexer(llm, embedder, vector_store)
index = indexer.index_file("presentation.pptx")
```

### PPTRetriever
Query the index.

```python
retriever = PPTRetriever(index, embedder)
results = retriever.search("query", top_k=5, method="hybrid")
```

### Core Classes
- **PPTParser** - Parse PPT files
- **StructureAnalyzer** - Detect hierarchy
- **SlideGraphBuilder** - Build graph structure
- **MetadataExtractor** - LLM-powered enrichment
- **IndexBuilder** - Assemble final index

## 🔐 Security & Best Practices

1. **Never hardcode API keys** - use environment variables
2. **Use secrets management** for production
3. **Validate input files** before processing
4. **Implement rate limiting** for LLM calls
5. **Store sensitive data** encrypted
6. **Monitor token usage** for cost control

## 🎁 Features Roadmap

- [ ] Web UI for indexing & querying
- [ ] Multi-modal retrieval (text + image search)
- [ ] Graph database integration (Neo4j)
- [ ] Fine-tuned embedding models
- [ ] Batch processing with queues
- [ ] Real-time streaming export
- [ ] Advanced analytics & insights
- [ ] Comparison matrix generation
- [ ] Auto-summary generation
- [ ] Interactive graph visualization

## 🤝 Contributing

Contributions welcome! Areas of interest:

- New plugin implementations
- Performance optimizations
- Advanced retrieval algorithms
- Better graph visualization
- Comprehensive examples

## 📄 License

MIT License - See LICENSE file

## 🙋 Support & Questions

- 📖 [Documentation](./docs)
- 💬 [GitHub Discussions](https://github.com/yourusername/pptx-indexer/discussions)
- 🐛 [Issue Tracker](https://github.com/yourusername/pptx-indexer/issues)

## 🌟 Citation

If you use PPTX Indexer in research, please cite:

```bibtex
@software{pptx_indexer2024,
  title={PPTX Indexer: Hierarchical PowerPoint Indexing Framework},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/pptx-indexer}
}
```

---

**Built with ❤️ for better document understanding**
