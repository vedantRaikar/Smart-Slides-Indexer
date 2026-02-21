"""Complete example: Query an indexed presentation.

This demonstrates the retrieval system with multiple search modes.
"""

import json
from pathlib import Path


def demo_retrieval():
    """Demonstrate retrieval on indexed presentation."""
    # Load index (assumes index_ppt.py was run first)
    INDEX_FILE = "./indexed_output/index.json"

    if not Path(INDEX_FILE).exists():
        print(f"Error: Index file not found at {INDEX_FILE}")
        print("Please run index_ppt.py first to create the index.")
        return

    print("Loading indexed presentation...")

    # Note: In production, you'd deserialize the DocumentIndex properly
    # For this demo, we'll load the JSON and show retrieval concepts
    with open(INDEX_FILE, "r") as f:
        index_data = json.load(f)

    print(f"Document: {index_data['document_title']}")
    print(f"Slides: {index_data['stats']['total_slides']}")
    print()

    # ===== Demonstration Queries =====
    queries = [
        "What are the main concepts?",
        "Tell me about the introduction",
        "Show me related content",
    ]

    print("=" * 60)
    print("RETRIEVAL DEMONSTRATION")
    print("=" * 60)

    for i, query in enumerate(queries, 1):
        print(f"\n[Query {i}] {query}")
        print("-" * 40)
        print("(In production, this would return ranked slides)")
        print("with semantic similarity scores and graph expansion)")
        print()

    # ===== Retrieval Modes =====
    print("\n" + "=" * 60)
    print("RETRIEVAL MODES AVAILABLE")
    print("=" * 60)

    modes = {
        "semantic": "Fast vector-based similarity search",
        "keyword": "Keyword/term matching across slides",
        "graph": "Graph traversal for structural relationships",
        "hybrid": "Combines semantic, keyword, and graph methods",
    }

    for mode, description in modes.items():
        print(f"\n✓ {mode.upper()}: {description}")

    print("\n" + "=" * 60)
    print("EXAMPLE CODE")
    print("=" * 60)

    example_code = """
from pptx_indexer.pipelines import PPTRetriever, PPTIndexer
from pptx_indexer.plugins.default_plugins import (
    OpenAILLM,
    SentenceTransformerEmbedder,
)

# Load your index (deserialized DocumentIndex)
index = load_index("index.json")

# Create retriever
embedder = SentenceTransformerEmbedder()
retriever = PPTRetriever(
    index=index,
    embedder=embedder,
)

# Semantic search
results = retriever.search(
    query="Explain machine learning",
    top_k=5,
    method="semantic",
)

for result in results:
    print(f"{result.slide_title}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Content: {result.slide_content[:100]}...")

# Graph-based search
results = retriever.search(
    query="Main concepts",
    method="graph",
    expand_graph=True,
)

# Get rich context around a slide
context = retriever.get_context(
    slide_id="slide_123",
    context_radius=2,
)
"""

    print(example_code)


if __name__ == "__main__":
    demo_retrieval()
    print("\n✓ Retrieval demonstration complete!")
