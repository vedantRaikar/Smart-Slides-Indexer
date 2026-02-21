"""Semantic retrieval from indexed PowerPoint presentation."""

import os
from pathlib import Path

from dotenv import load_dotenv

from pptx_indexer.plugins.default_plugins import (
    GroqLLM,
    SentenceTransformerEmbedder,
    ChromaVectorStore,
)

load_dotenv()


def load_index(output_dir: str = "./indexed_output"):
    """Load the indexed presentation data."""
    import json
    
    index_path = Path(output_dir) / "index.json"
    with open(index_path, "r") as f:
        return json.load(f)


def create_slide_text(slide: dict) -> str:
    """Combine slide content into a single text for embedding."""
    parts = []
    
    if slide.get("title"):
        parts.append(f"Title: {slide['title']}")
    if slide.get("subtitle"):
        parts.append(f"Subtitle: {slide['subtitle']}")
    if slide.get("bullets"):
        bullet_texts = []
        for bullet in slide["bullets"]:
            if isinstance(bullet, dict):
                bullet_texts.append(bullet.get("text", ""))
            else:
                bullet_texts.append(str(bullet))
        parts.append("Content: " + " | ".join(bullet_texts))
    if slide.get("summary"):
        parts.append(f"Summary: {slide['summary']}")
    if slide.get("keywords"):
        parts.append(f"Keywords: {', '.join(slide['keywords'])}")
    if slide.get("learning_objectives"):
        parts.append("Learning Objectives: " + " | ".join(slide["learning_objectives"]))
    
    return " | ".join(parts)


def semantic_search(query: str, index_data: dict, embedder, top_k: int = 3) -> list:
    """Search for most relevant slides based on query."""
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    
    slides = index_data["slides"]
    slide_texts = [create_slide_text(slide) for slide in slides.values()]
    slide_ids = list(slides.keys())
    
    query_embedding = embedder.embed([query])[0]
    slide_embeddings = embedder.embed(slide_texts)
    
    similarities = cosine_similarity([query_embedding], slide_embeddings)[0]
    
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        slide_id = slide_ids[idx]
        slide = slides[slide_id]
        results.append({
            "slide_id": slide_id,
            "slide_number": slide["slide_number"],
            "title": slide.get("title", ""),
            "content": slide_texts[idx],
            "score": float(similarities[idx]),
        })
    
    return results


def answer_question(query: str, results: list, llm) -> str:
    """Use LLM to answer question based on retrieved slides."""
    context_parts = []
    for r in results:
        context_parts.append(
            f"Slide {r['slide_number']}: {r['title']}\n{r['content']}"
        )
    
    context = "\n\n".join(context_parts)
    
    prompt = f"""Based on the following presentation content, answer the question.

Presentation Content:
{context}

Question: {query}

Answer the question based only on the presentation content above. If the answer is not in the content, say so."""
    
    return llm.generate(prompt)


def main():
    """Main retrieval example."""
    print("Loading index...")
    index_data = load_index("./indexed_output")
    print(f"Loaded presentation: {index_data['document_title']}")
    print(f"Total slides: {index_data['stats']['total_slides']}")
    
    print("\nInitializing embedder...")
    embedder = SentenceTransformerEmbedder(model="all-MiniLM-L6-v2")
    
    print("\nInitializing LLM...")
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("Warning: GROQ_API_KEY not set. LLM features will be disabled.")
        llm = None
    else:
        llm = GroqLLM(api_key=groq_key, model="openai/gpt-oss-120b")
    
    print("\n" + "=" * 60)
    print("Semantic Retrieval - Ask questions about your presentation")
    print("=" * 60)
    print("Type 'quit' or 'exit' to stop\n")
    
    while True:
        query = input("Enter your question: ").strip()
        
        if query.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        if not query:
            continue
        
        print("\nSearching for relevant slides...")
        results = semantic_search(query, index_data, embedder, top_k=3)
        
        print(f"\nFound {len(results)} relevant slides:")
        for r in results:
            print(f"  - Slide {r['slide_number']}: {r['title']} (score: {r['score']:.3f})")
        
        if llm is not None:
            print("\nGenerating answer...")
            answer = answer_question(query, results, llm)
            print(f"\nAnswer:\n{answer}")
        else:
            print("\nNo LLM available - showing relevant slides only")
        
        print()


if __name__ == "__main__":
    main()
