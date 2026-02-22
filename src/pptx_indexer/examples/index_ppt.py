"""Complete example: Index a PowerPoint presentation.

This demonstrates the full PPTX Indexer workflow:
1. Parse presentation
2. Analyze structure
3. Extract metadata
4. Build graph index
5. Export for retrieval
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from pptx_indexer.config import IndexingConfig

# Import indexer components
from pptx_indexer.pipelines.indexing_pipeline import PPTIndexer
from pptx_indexer.plugins.default_plugins import (
    ChromaVectorStore,
    GroqLLM,
    PaddleOCR,
    SentenceTransformerEmbedder,
)


def main():
    # Load environment variables from .env file
    load_dotenv()
    """Main example - index a presentation."""
    # ===== Configuration =====
    PPTX_FILE = "sample_presentation.pptx"  # Replace with your file
    OUTPUT_DIR = "./indexed_output"

    # Check if file exists
    if not Path(PPTX_FILE).exists():
        print(f"Error: {PPTX_FILE} not found. Please provide a PowerPoint file.")
        return

    # ===== Initialize plugins =====
    print("Initializing plugins...")

    # LLM for metadata extraction
    # Option 3: Groq
    llm = GroqLLM(api_key=os.getenv("GROQ_API_KEY"), model="openai/gpt-oss-120b")

    # Embedder for semantic search
    embedder = SentenceTransformerEmbedder(model="all-MiniLM-L6-v2")

    # Vector store for fast retrieval
    vector_store = ChromaVectorStore(collection_name="presentation_index")

    # OCR for image text extraction
    ocr = PaddleOCR()

    # ===== Create indexer =====
    print("Creating indexer...")

    indexer = PPTIndexer(
        llm=llm,
        embedder=embedder,
        vector_store=vector_store,
        ocr=ocr,
        config=IndexingConfig(
            enable_ocr=True,
            generate_summaries=True,
            compute_similarity_matrix=True,
        ),
    )

    # ===== Index the presentation =====
    print(f"Indexing presentation: {PPTX_FILE}")

    try:
        index = indexer.index_file(
            pptx_path=PPTX_FILE,
            output_dir=OUTPUT_DIR,
        )
    except Exception as e:
        print(f"Error during indexing: {e}")
        return

    # ===== Display results =====
    print("\n" + "=" * 60)
    print("INDEXING COMPLETE")
    print("=" * 60)

    print(f"\nDocument: {index.document_title}")
    print(f"Total slides: {index.stats.total_slides}")
    print(f"Total sections: {index.stats.total_sections}")
    print(f"Total images: {index.stats.total_images}")
    print(f"Estimated reading time: {index.stats.estimated_reading_time_minutes} minutes")

    print("\nTop keywords:")
    for keyword, count in sorted(
        [(k, len(v)) for k, v in index.keyword_to_slides.items()], key=lambda x: x[1], reverse=True
    )[:10]:
        print(f"  - {keyword}: {count} slides")

    print("\nSections detected:")
    for section in index.sections.values():
        print(f"  - {section.title} ({len(section.slide_ids)} slides)")

    print("\nGraph statistics:")
    if index.graph:
        print(f"  - Graph nodes: {len(index.graph.nodes)}")
        print(f"  - Graph edges: {len(index.graph.edges)}")

    print(f"\nOutput saved to: {OUTPUT_DIR}")

    return index


if __name__ == "__main__":
    index = main()
    print("\n✓ Example complete!")
