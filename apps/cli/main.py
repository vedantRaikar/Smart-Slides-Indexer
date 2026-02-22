"""Command-line interface for Smart Slides Indexer.

Usage:
    ssi index input.pptx                    # Index a PPTX file
    ssi search "query"                      # Search indexed presentations
    ssi serve                               # Start API server
    ssi --version                           # Show version
"""

import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from apps.worker.indexing import IndexerWorker
from pptx_indexer.config import get_config
from pptx_indexer.vector_store import create_vector_store

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def cmd_index(args):
    """Index a PPTX file."""
    setup_logging(args.log_level)

    if not Path(args.input).exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    output_dir = args.output or "./data/output"

    print(f"Indexing: {args.input}")
    print(f"Output: {output_dir}")

    worker = IndexerWorker()
    context = worker.process(
        input_path=args.input,
        output_dir=output_dir,
        job_id=args.job_id,
    )

    print("\n[+] Indexing complete!")
    print(f"  Slides: {len(context.slides)}")
    print(f"  Sections: {context.metadata.get('total_sections', 0)}")
    print(f"  Output: {output_dir}")

    # Show sample keywords
    if context.slides:
        keywords = context.slides[0].get("keywords", [])
        if keywords:
            print(f"  Sample keywords: {', '.join(keywords[:5])}")


def cmd_search(args):
    """Search indexed presentations."""
    setup_logging(args.log_level)

    config = get_config()

    # Initialize vector store
    vector_store = create_vector_store(
        collection_name=args.collection or config.vector_store.collection_name,
    )

    # Get query embedding
    from sentence_transformers import SentenceTransformer

    print(f"Searching for: {args.query}")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode(args.query).tolist()

    # Search
    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=args.top_k,
    )

    if not results:
        print("No results found.")
        return

    print(f"\nFound {len(results)} results:\n")
    for i, r in enumerate(results, 1):
        print(
            f"{i}. Slide {r.metadata.get('slide_number', '?')}: {r.metadata.get('title', 'Untitled')}"
        )
        print(f"   Score: {r.score:.3f}")
        print(f"   {r.text[:200]}...")
        print()


def cmd_serve(args):
    """Start the API server."""
    import uvicorn
    from api.main import app

    config = get_config()

    uvicorn.run(
        app,
        host=args.host or config.api_host,
        port=args.port or config.api_port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


def cmd_info(args):
    """Show configuration info."""
    config = get_config()

    print("Smart Slides Indexer Configuration")
    print("=" * 40)
    print(f"App: {config.app_name}")
    print(f"Environment: {config.environment}")
    print()
    print("LLM Provider:")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Model: {config.llm.model}")
    print(f"  Cache: {config.llm.cache_enabled}")
    print()
    print("Embedder:")
    print(f"  Model: {config.embedder.model}")
    print(f"  Device: {config.embedder.device}")
    print()
    print("Vector Store:")
    print(f"  Provider: {config.vector_store.provider}")
    print(f"  Collection: {config.vector_store.collection_name}")
    print()
    print("OCR:")
    print(f"  Provider: {config.ocr.provider}")
    print(f"  Enabled: {config.ocr.enabled}")


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Smart Slides Indexer - Index and search PowerPoint presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Smart Slides Indexer 1.0.0",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index a PPTX file")
    index_parser.add_argument("input", help="Input PPTX file path")
    index_parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: ./data/output)",
    )
    index_parser.add_argument(
        "--job-id",
        help="Job ID for idempotent processing",
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="Search indexed presentations")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)",
    )
    search_parser.add_argument(
        "-c",
        "--collection",
        help="Collection name to search",
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument(
        "--host",
        help="Host to bind (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        help="Port to bind (default: 8000)",
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload",
    )

    # Info command
    subparsers.add_parser("info", help="Show configuration info")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "index":
        cmd_index(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "info":
        cmd_info(args)


if __name__ == "__main__":
    main()
