"""
PPTX Indexer - Comprehensive Integration Guide
"""

# TABLE OF CONTENTS
# 1. Integration Scenarios
# 2. LLM/RAG Integration
# 3. Web Framework Integration
# 4. Data Pipeline Integration
# 5. Multi-Source Indexing
# 6. Advanced Query Patterns


# 1. INTEGRATION SCENARIOS

## Scenario A: Standalone Indexing Service

Use case: Index PowerPoints and save indices for later retrieval

```python
# index_and_save.py
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import *
import json

# Setup
indexer = PPTIndexer(
    llm=OpenAILLM(api_key="sk-..."),
    embedder=SentenceTransformerEmbedder(),
    vector_store=ChromaVectorStore(),
)

# Index multiple presentations
presentations = [
    "ai_fundamentals.pptx",
    "machine_learning_101.pptx",
    "deep_learning_advanced.pptx",
]

indices = {}
for ppt_file in presentations:
    print(f"Indexing {ppt_file}...")
    index = indexer.index_file(ppt_file, output_dir="./data")
    indices[ppt_file] = index
    
    # Save index
    with open(f"./data/{ppt_file}.json", "w") as f:
        json.dump(index.to_dict(), f, indent=2, default=str)
    
    print(f"✓ {ppt_file}: {len(index.slides)} slides, {len(index.sections)} sections")

print(f"\nIndexed {len(indices)} presentations")
```


## Scenario B: Real-Time Query Service

Use case: Load indices and answer queries on demand

```python
# query_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from pptx_indexer.pipelines import PPTRetriever
from pptx_indexer.schemas.document_index import DocumentIndex

app = FastAPI()

# Load indices at startup
indices = {}

def load_indices():
    """Load all saved indices."""
    import glob
    for index_file in glob.glob("./data/*.json"):
        doc_name = index_file.split("/")[-1]
        with open(index_file) as f:
            data = json.load(f)
            indices[doc_name] = DocumentIndex.from_dict(data)

load_indices()
print(f"Loaded {len(indices)} indices")

# Initialize retriever
from pptx_indexer.plugins.default_plugins import SentenceTransformerEmbedder
embedder = SentenceTransformerEmbedder()

class QueryRequest(BaseModel):
    query: str
    presentation: str = None  # None = search all
    method: str = "hybrid"
    top_k: int = 5

class QueryResult(BaseModel):
    presentation: str
    slide_id: str
    title: str
    score: float
    content: str

@app.post("/query")
async def query(request: QueryRequest) -> List[QueryResult]:
    """Query indexed presentations."""
    all_results = []
    
    # Search specified or all indices
    search_indices = (
        {request.presentation: indices[request.presentation]}
        if request.presentation
        else indices
    )
    
    for doc_name, index in search_indices.items():
        retriever = PPTRetriever(index, embedder)
        results = retriever.search(
            request.query,
            method=request.method,
            top_k=request.top_k,
        )
        
        for result in results:
            all_results.append(QueryResult(
                presentation=doc_name,
                slide_id=result.slide_id,
                title=result.title,
                score=result.score,
                content=result.content,
            ))
    
    # Sort by score
    all_results.sort(key=lambda x: x.score, reverse=True)
    return all_results[:request.top_k]

@app.get("/presentations")
async def list_presentations():
    """List available presentations."""
    return list(indices.keys())

# Run: uvicorn query_service:app --reload
# Query: curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "What is AI?", "method": "hybrid"}'
```


## Scenario C: Document Question Answering (DocQA)

Use case: Answer questions about presentations using LLM + retrieval

```python
# docqa.py
from pptx_indexer import PPTIndexer
from pptx_indexer.pipelines import PPTRetriever
from pptx_indexer.plugins.default_plugins import *
import openai

class DocumentQA:
    """Question Answering over presentations."""
    
    def __init__(self, openai_api_key: str):
        self.indexer = PPTIndexer(
            llm=OpenAILLM(api_key=openai_api_key),
            embedder=SentenceTransformerEmbedder(),
            vector_store=ChromaVectorStore(),
        )
        self.openai_api_key = openai_api_key
    
    def index_presentation(self, ppt_file: str):
        """Index a presentation."""
        self.index = self.indexer.index_file(ppt_file)
        self.retriever = PPTRetriever(self.index, self.indexer.embedder)
    
    def answer_question(self, question: str, top_k: int = 3) -> str:
        """Answer question using RAG."""
        # 1. Retrieve relevant slides
        results = self.retriever.search(
            question,
            method="hybrid",
            top_k=top_k,
        )
        
        # 2. Build context
        context_parts = []
        for result in results:
            context_parts.append(f"Slide {result.slide_id}: {result.content}")
        context = "\n\n".join(context_parts)
        
        # 3. Query LLM
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant answering questions based on presentation content.",
                },
                {
                    "role": "user",
                    "content": f"Context from presentation:\n{context}\n\nQuestion: {question}",
                },
            ],
            temperature=0.7,
        )
        
        return response["choices"][0]["message"]["content"]

# Usage
qa = DocumentQA(openai_api_key="sk-...")
qa.index_presentation("presentation.pptx")

answer = qa.answer_question("What are the key takeaways?")
print(answer)

# Multi-turn conversation
print(qa.answer_question("Can you elaborate on the first point?"))
print(qa.answer_question("How does this relate to the next section?"))
```


# 2. LLM/RAG INTEGRATION

## Extending for RAG Systems

```python
# rag_integration.py
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

class PPTRAGChain:
    """LangChain integration for PP retrieval augmented generation."""
    
    def __init__(self, index, embedder, openai_api_key: str):
        self.index = index
        self.embedder = embedder
        self.retriever = PPTRetriever(index, embedder)
        
        # Initialize LangChain
        self.llm = OpenAI(
            temperature=0.7,
            openai_api_key=openai_api_key,
        )
        self.memory = ConversationBufferMemory()
    
    def _format_context(self, query: str) -> str:
        """Retrieve and format context."""
        results = self.retriever.search(query, method="hybrid", top_k=3)
        context = "\n".join([
            f"[Slide {r.slide_id}]: {r.content[:500]}"
            for r in results
        ])
        return context
    
    def chat(self, user_input: str) -> str:
        """Chat with RAG context."""
        # Retrieve context
        context = self._format_context(user_input)
        
        # Build prompt
        prompt = f"""
You are a knowledgeable assistant about this presentation.

Context from presentation:
{context}

Question: {user_input}

Answer based on the context above:
"""
        
        # Get response
        response = self.llm(prompt)
        
        # Store in memory
        self.memory.save_context(
            {"input": user_input},
            {"output": response},
        )
        
        return response

# Usage with conversation
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import *

indexer = PPTIndexer(...)
index = indexer.index_file("ml_course.pptx")

rag = PPTRAGChain(
    index,
    indexer.embedder,
    openai_api_key="sk-...",
)

# Multi-turn conversation
print(rag.chat("What is deep learning?"))
print(rag.chat("How is it different from machine learning?"))
print(rag.chat("Can you give an example?"))
```


## DSPy Integration (Advanced)

```python
# dspy_integration.py
import dspy
from pptx_indexer.pipelines import PPTRetriever

class SlideRetrievalModule(dspy.ChainOfThought):
    """DSPy module for slide retrieval."""
    
    class Input(dspy.Signature):
        query: str = dspy.InputField()
        context: str = dspy.InputField(desc="Retrieved slide content")
    
    class Output(dspy.Signature):
        answer: str = dspy.OutputField(desc="Answer to query")
    
    def __init__(self, retriever: PPTRetriever):
        super().__init__()
        self.retriever = retriever
    
    def forward(self, query: str) -> str:
        # Retrieve context
        results = self.retriever.search(query, top_k=3)
        context = "\n".join([r.content for r in results])
        
        # Generate answer
        response = super().forward(query=query, context=context)
        return response.answer

# Usage
dspy.settings.configure(lm=dspy.OpenAI(model="gpt-4"))

module = SlideRetrievalModule(retriever)
answer = module.forward("What are the main concepts?")
```


# 3. WEB FRAMEWORK INTEGRATION

## Flask Integration

```python
# app_flask.py
from flask import Flask, request, jsonify
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import *

app = Flask(__name__)

# Initialize at startup
indexer = PPTIndexer(
    llm=OpenAILLM(api_key="sk-..."),
    embedder=SentenceTransformerEmbedder(),
    vector_store=ChromaVectorStore(),
)

indices = {}

@app.route("/upload", methods=["POST"])
def upload():
    """Upload and index presentation."""
    file = request.files["file"]
    file.save(file.filename)
    
    try:
        index = indexer.index_file(file.filename)
        indices[file.filename] = index
        
        return jsonify({
            "status": "success",
            "document_id": index.document_id,
            "slides": len(index.slides),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/search", methods=["POST"])
def search():
    """Search presentations."""
    data = request.json
    query = data["query"]
    doc_name = data.get("document")
    
    if doc_name and doc_name not in indices:
        return jsonify({"error": "Document not found"}), 404
    
    from pptx_indexer.pipelines import PPTRetriever
    
    all_results = []
    for name, index in (
        {doc_name: indices[doc_name]}.items()
        if doc_name
        else indices.items()
    ):
        retriever = PPTRetriever(index, indexer.embedder)
        results = retriever.search(query, top_k=5)
        
        for r in results:
            all_results.append({
                "document": name,
                "slide_id": r.slide_id,
                "title": r.title,
                "score": r.score,
                "content": r.content[:500],
            })
    
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(all_results[:5])

if __name__ == "__main__":
    app.run(debug=True)
```


## Django Integration

```python
# django_integration.py
from django.views import View
from django.http import JsonResponse
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import *

# models.py
from django.db import models

class Presentation(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="presentations/")
    document_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class SearchResult(models.Model):
    presentation = models.ForeignKey(Presentation, on_delete=models.CASCADE)
    query = models.TextField()
    results = models.JSONField()  # Store search results
    created_at = models.DateTimeField(auto_now_add=True)

# views.py
from django.shortcuts import render
from django.views.decorators.http import require_POST

indexer = PPTIndexer(...)

@require_POST
def upload_presentation(request):
    """Upload and index presentation."""
    file = request.FILES["file"]
    
    try:
        # Index
        index = indexer.index_file(file.name)
        
        # Save to DB
        presentation = Presentation.objects.create(
            name=file.name,
            file=file,
            document_id=index.document_id,
        )
        
        return JsonResponse({
            "status": "success",
            "id": presentation.id,
            "slides": len(index.slides),
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@require_POST
def search_presentations(request):
    """Search presentations."""
    query = request.POST["query"]
    
    from pptx_indexer.pipelines import PPTRetriever
    
    results_list = []
    for presentation in Presentation.objects.all():
        # Load index from file
        import json
        with open(f"./data/{presentation.document_id}.json") as f:
            index_data = json.load(f)
        
        index = DocumentIndex.from_dict(index_data)
        retriever = PPTRetriever(index, indexer.embedder)
        
        results = retriever.search(query, top_k=3)
        
        for r in results:
            results_list.append({
                "presentation_id": presentation.id,
                "presentation_name": presentation.name,
                "slide_id": r.slide_id,
                "content": r.content[:300],
                "score": float(r.score),
            })
    
    # Save search to DB
    SearchResult.objects.create(
        presentation=Presentation.objects.first(),  # Adjust logic
        query=query,
        results=results_list,
    )
    
    return JsonResponse(results_list[:5])
```


# 4. DATA PIPELINE INTEGRATION

## Apache Airflow DAG

```python
# dags/ppt_indexing_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

default_args = {"start_date": datetime(2024, 1, 1)}

dag = DAG("ppt_indexing", default_args=default_args, schedule_interval="daily")

def index_presentations():
    """Index all presentations in input folder."""
    from pptx_indexer import PPTIndexer
    from pptx_indexer.plugins.default_plugins import *
    import glob
    
    indexer = PPTIndexer(
        llm=OpenAILLM(api_key="sk-..."),
        embedder=SentenceTransformerEmbedder(),
        vector_store=ChromaVectorStore(),
    )
    
    for ppt_file in glob.glob("./input/*.pptx"):
        index = indexer.index_file(ppt_file, output_dir="./output")
        print(f"✓ Indexed {ppt_file}")

def upload_to_storage():
    """Upload indices to cloud storage."""
    import boto3
    s3 = boto3.client('s3')
    
    for file in glob.glob("./output/*.json"):
        s3.upload_file(file, "my-bucket", file)

task1 = PythonOperator(
    task_id="index_presentations",
    python_callable=index_presentations,
    dag=dag,
)

task2 = PythonOperator(
    task_id="upload_to_storage",
    python_callable=upload_to_storage,
    dag=dag,
)

task1 >> task2
```


## Prefect Flow

```python
# prefect_flow.py
from prefect import flow, task
import glob

@task
def index_single_presentation(ppt_file: str):
    """Index a single presentation."""
    from pptx_indexer import PPTIndexer
    from pptx_indexer.plugins.default_plugins import *
    
    indexer = PPTIndexer(...)
    index = indexer.index_file(ppt_file)
    return index.document_id

@task
def upload_indices():
    """Upload all indices."""
    import boto3
    s3 = boto3.client('s3')
    for file in glob.glob("./output/*.json"):
        s3.upload_file(file, "bucket", file)

@flow
def index_and_upload_flow():
    """Main workflow."""
    files = glob.glob("./input/*.pptx")
    
    # Index in parallel
    document_ids = [index_single_presentation.map(f) for f in files]
    
    # Upload
    upload_indices()
    
    return document_ids

# Run
if __name__ == "__main__":
    index_and_upload_flow()
```


# 5. MULTI-SOURCE INDEXING

## Index Multiple Presentations

```python
# multi_index.py
from pptx_indexer import PPTIndexer
from pptx_indexer.plugins.default_plugins import *
from pptx_indexer.schemas.document_index import DocumentIndex
import glob

# Initialize
indexer = PPTIndexer(
    llm=OpenAILLM(...),
    embedder=SentenceTransformerEmbedder(),
    vector_store=ChromaVectorStore(),
)

# Index all PPTs
all_indices = []
for ppt_file in glob.glob("./presentations/*.pptx"):
    print(f"Indexing {ppt_file}...")
    index = indexer.index_file(ppt_file)
    all_indices.append(index)

# Create merged index for cross-presentation search
class MergedIndex:
    def __init__(self, indices: List[DocumentIndex]):
        self.indices = indices
    
    def search(self, query: str, top_k: int = 10):
        """Search across all presentations."""
        from pptx_indexer.pipelines import PPTRetriever
        
        all_results = []
        for index in self.indices:
            retriever = PPTRetriever(index, indexer.embedder)
            results = retriever.search(query, top_k=top_k)
            all_results.extend(results)
        
        # Sort by score
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]

merged = MergedIndex(all_indices)
results = merged.search("Key concept")
```


# 6. ADVANCED QUERY PATTERNS

## Complex Filtering

```python
# advanced_queries.py
class AdvancedRetriever:
    """Advanced retrieval with filtering."""
    
    def search_with_filters(
        self,
        query: str,
        min_score: float = 0.3,
        section_filter: str = None,
        slide_range: tuple = None,  # (start, end)
    ):
        """Search with multiple filters."""
        results = self.retriever.search(query, top_k=100)
        
        # Filter by score
        results = [r for r in results if r.score >= min_score]
        
        # Filter by section
        if section_filter:
            results = [
                r for r in results
                if section_filter in self.index.slides[r.slide_id].section_id
            ]
        
        # Filter by slide range
        if slide_range:
            start, end = slide_range
            results = [
                r for r in results
                if start <= int(r.slide_id) <= end
            ]
        
        return results

    def semantic_clustering(self, query: str, num_clusters: int = 5):
        """Return results grouped by semantic similarity."""
        from sklearn.cluster import KMeans
        
        results = self.retriever.search(query, top_k=50)
        embeddings = [
            self.retriever.embedder.embed(r.content)
            for r in results
        ]
        
        kmeans = KMeans(n_clusters=num_clusters)
        clusters = kmeans.fit_predict(embeddings)
        
        grouped = {}
        for i, result in enumerate(results):
            cluster_id = int(clusters[i])
            if cluster_id not in grouped:
                grouped[cluster_id] = []
            grouped[cluster_id].append(result)
        
        return grouped

    def comparative_search(
        self,
        query1: str,
        query2: str,
    ):
        """Compare results for two queries."""
        results1 = self.retriever.search(query1, top_k=5)
        results2 = self.retriever.search(query2, top_k=5)
        
        return {
            "query1": [r.to_dict() for r in results1],
            "query2": [r.to_dict() for r in results2],
            "overlap": [
                r for r in results1
                if r.slide_id in [r2.slide_id for r2 in results2]
            ],
        }
```


## Summary

For more details, check:
- `README_PPTX_INDEXER.md` - Main documentation
- `ARCHITECTURE.md` - System design
- `DEPLOYMENT.md` - Production setup
- `CUSTOM_PLUGINS.md` - Extending framework
- Code comments in each module
