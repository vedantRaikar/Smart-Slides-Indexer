"""
Architecture & Design Documentation for PPTX Indexer
"""

# ARCHITECTURE OVERVIEW

## Pipeline Stages

### Stage 1: PARSE (PPTParser)
Input: PowerPoint file (.pptx)
Output: List[SlideNode]

Functions:
- Extract titles and subtitles
- Parse hierarchical bullet points (preserve levels)
- Extract images and save to disk
- Extract tables with structure
- Extract speaker notes
- Identify layout type

Key classes:
- SlideNode: Complete slide representation
- BulletPoint: Hierarchical bullet structure
- ImageNode: Image metadata
- TableNode: Table structure


### Stage 2: ANALYZE (StructureAnalyzer)
Input: List[SlideNode]
Output: List[SectionNode], Dict[slide_id -> section_id]

Functions:
- Detect section boundaries using multiple heuristics
- Build hierarchical organization
- Identify topics and subtopics
- Compute slide-to-slide similarity
- Detect transitions and structural breaks

Heuristics for section detection:
1. Pattern matching (Part X, Chapter Y, etc)
2. Title-only slides (no bullets = section title)
3. Semantic similarity clustering
4. Layout change detection


### Stage 3: GRAPH (SlideGraphBuilder)
Input: List[SlideNode], List[SectionNode], similarity matrix
Output: SlideGraph

Functions:
- Create graph nodes for slides/sections
- Add sequential edges (NEXT, PREVIOUS)
- Add hierarchical edges (BELONGS_TO, CONTAINS)
- Add semantic edges (SIMILAR, RELATED)
- Add reference edges (REFERENCES)

Graph structure:
- Nodes: slides, sections, concepts, images
- Edges: typed relationships with weights
- Supports multi-hop traversal
- Enables graph-based retrieval


### Stage 4: METADATA (MetadataExtractor)
Input: List[SlideNode], LLM instance
Output: Enriched SlideNode with keywords, topics, summaries

Functions:
- Extract keywords using LLM
- Identify main topics
- Generate slide summaries
- Extract learning objectives (if educational)
- Extract named entities
- Process image captions and OCR

LLM prompts:
- "Extract top keywords from this text"
- "What are the main topics?"
- "Summarize this slide in one sentence"
- "Are there learning objectives?"


### Stage 5: INDEX (IndexBuilder)
Input: Slides, Sections, Graph, Metadata
Output: DocumentIndex

Functions:
- Generate embeddings for all content
- Store vectors in vector store
- Build search indices
- Compute statistics
- Export in multiple formats

Embeddings created:
- Slide embeddings (full content)
- Title embeddings (semantic search on titles)
- Section embeddings
- Document embedding (mean of all)
- Image embeddings


## Key Design Decisions

### 1. NO CHUNKING
Instead of splitting content into chunks, we:
- Preserve complete slides as units
- Use hierarchical structure (bullets)
- Create graph relationships for traversal
- Support multi-resolution queries

### 2. SEMANTIC PRESERVATION
- Extract hierarchy from bullet levels
- Preserve slide sequence
- Detect logical grouping
- Maintain visual-semantic relationships

### 3. PLUGGABLE ARCHITECTURE
- All LLMs, embedders, stores are pluggable
- Abstract base classes define interfaces
- Dependency injection throughout
- Easy to swap implementations

### 4. MULTI-RESOLUTION INDEXING
- Document level: mean embedding
- Section level: section embeddings
- Slide level: full + title embeddings
- Query at any level

### 5. GRAPH-BASED RETRIEVAL
- Fast semantic search via vectors
- Rich traversal via graph relationships
- Context expansion from neighbors
- Multiple retrieval strategies (hybrid)


## Data Flow

```
presentation.pptx
        ↓
   [PARSE]
        ↓
  List[SlideNode]
        ↓
  [ANALYZE Structure]
        ↓
  List[SectionNode]
        ↓
  [BUILD Graph]
        ↓
   SlideGraph
        ↓
  [EXTRACT Metadata]
        ↓
  [GENERATE Embeddings]
        ↓
  [STORE Vectors]
        ↓
  DocumentIndex ← Ready for Retrieval
```


## Component Interactions

```
PPTIndexer (Orchestrator)
    │
    ├─→ PPTParser
    │       └─→ SlideNode[]
    │
    ├─→ StructureAnalyzer
    │       └─→ SectionNode[]
    │
    ├─→ SlideGraphBuilder
    │       └─→ SlideGraph
    │
    ├─→ MetadataExtractor (uses LLM)
    │       └─→ Enriched SlideNode
    │
    ├─→ IndexBuilder (uses Embedder + VectorStore)
    │       └─→ DocumentIndex
    │
    └─→ Export (JSON, JSONL, Pickle)


PPTRetriever (Query Time)
    │
    ├─→ Embedder (embed query)
    ├─→ VectorStore (semantic search)
    ├─→ SlideGraph (traverse relationships)
    └─→ DocumentIndex (fetch content)
            └─→ RetrievalResult[]
```


## Extensibility Points

### Add New LLM Provider
1. Inherit from BaseLLM
2. Implement generate() and batch_generate()
3. Pass to PPTIndexer.__init__()

### Add New Embedder
1. Inherit from BaseEmbedder
2. Implement embed() and batch_embed()
3. Set embedding_dim property
4. Pass to PPTIndexer.__init__()

### Add New Vector Store
1. Inherit from BaseVectorStore
2. Implement add(), search(), batch_search(), delete()
3. Pass to PPTIndexer.__init__()

### Add New OCR Engine
1. Inherit from BaseOCR
2. Implement extract_text()
3. Pass to PPTIndexer.__init__()

### Custom Processing
1. Subclass PPTIndexer or components
2. Override _extract_metadata(), _build_graph(), etc
3. Or create new pipeline stages


## Performance Considerations

### Memory Usage
- Embeddings: 768-1536 dims × 4 bytes = 3-6 KB per slide
- 1000 slides: ~3-6 MB embeddings
- Vectors stored in specialized vector DB (compressed)

### Speed Optimization
- Batch embeddings: 32+ at a time
- Parallel processing: 4+ workers
- Caching: reuse embeddings
- Filter: early stopping in search

### Scalability
- ✓ Works with 100s of slides
- ✓ Can be extended to 1000s
- ✓ Graph traversal stays fast with proper indexing
- ✓ Vector search sub-second for <100K docs


## Quality Metrics

Track these during indexing:
1. **Coverage**: % of content with embeddings
2. **Hierarchy Quality**: # of detected sections vs manual
3. **Embedding Quality**: cosine similarity distribution
4. **Retrieval Quality**: NDCG@5, MRR metrics

---

For implementation details, see code comments in each module.
