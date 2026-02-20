"""
Complete indexing pipeline for PPTX documents.
Orchestrates all components: parsing, structure analysis, graph building,
metadata extraction, and index creation.

This is THE entry point for the entire framework.
"""

import uuid
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from ..config import IndexingConfig
from ..plugins.base_llm import (
    PluginRegistry,
    BaseLLM,
    BaseEmbedder,
    BaseVectorStore,
    BaseOCR,
    BaseImageCaptioner,
)
from ..core.parser import PPTParser
from ..core.structure_analyzer import StructureAnalyzer
from ..core.slide_graph import SlideGraphBuilder
from ..core.metadata_extractor import MetadataExtractor
from ..core.index_builder import IndexBuilder
from ..schemas.document_index import DocumentIndex

logger = logging.getLogger(__name__)


class PPTIndexer:
    """
    Complete indexing pipeline for PowerPoint presentations.
    
    Pipeline stages:
    1. Parse PPT -> SlideNodes
    2. Analyze structure -> SectionNodes
    3. Build graph -> SlideGraph
    4. Extract metadata -> Enriched SlideNodes/SectionNodes
    5. Build index -> DocumentIndex
    
    Example:
        indexer = PPTIndexer(
            llm=OpenAILLM(api_key="..."),
            embedder=SentenceTransformerEmbedder(),
            vector_store=ChromaStore()
        )
        
        index = indexer.index_file("presentation.pptx")
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        embedder: BaseEmbedder,
        vector_store: Optional[BaseVectorStore] = None,
        ocr: Optional[BaseOCR] = None,
        image_captioner: Optional[BaseImageCaptioner] = None,
        config: Optional[IndexingConfig] = None,
    ):
        """
        Initialize indexer with plugins.
        
        Args:
            llm: LLM for metadata extraction
            embedder: Embedding model
            vector_store: Vector database (optional but recommended)
            ocr: OCR engine (optional)
            image_captioner: Image captioning model (optional)
            config: Indexing configuration
        """
        self.config = config or IndexingConfig()
        
        # Register plugins
        self.plugins = PluginRegistry(
            llm=llm,
            embedder=embedder,
            vector_store=vector_store,
            ocr=ocr,
            image_captioner=image_captioner,
        )
        
        if not self.plugins.validate():
            raise ValueError("LLM and Embedder are required")
        
        # Initialize core components
        self.parser = PPTParser()
        self.structure_analyzer = StructureAnalyzer()
        self.graph_builder = SlideGraphBuilder()
        self.metadata_extractor = MetadataExtractor(llm)
        self.index_builder = IndexBuilder(
            embedder=embedder,
            vector_store=vector_store,
            ocr=ocr,
            image_captioner=image_captioner,
        )
        
        logger.info("PPTIndexer initialized")
    
    def index_file(self, pptx_path: str, output_dir: Optional[str] = None) -> DocumentIndex:
        """
        Index a PowerPoint file.
        
        Args:
            pptx_path: Path to .pptx file
            output_dir: Optional directory for outputs
        
        Returns:
            Complete DocumentIndex
        """
        logger.info(f"Starting indexing of: {pptx_path}")
        
        # Validate file
        if not pptx_path.lower().endswith('.pptx'):
            raise ValueError("File must be .pptx format")
        
        if not Path(pptx_path).exists():
            raise FileNotFoundError(f"File not found: {pptx_path}")
        
        # Generate document ID and setup output
        document_id = str(uuid.uuid4())
        document_title = Path(pptx_path).stem
        
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Stage 1: Parse
        logger.info("Stage 1: Parsing presentation...")
        slides = self.parser.parse(pptx_path)
        logger.info(f"✓ Parsed {len(slides)} slides")
        
        # Stage 2: Analyze structure
        logger.info("Stage 2: Analyzing structure...")
        sections, slide_to_section = self.structure_analyzer.analyze(slides)
        logger.info(f"✓ Detected {len(sections)} sections")
        
        # Assign sections to slides
        for slide in slides:
            if slide.slide_id in slide_to_section:
                slide.section_id = slide_to_section[slide.slide_id]
        
        # Stage 3: Build graph
        logger.info("Stage 3: Building slide graph...")
        
        similarities = self.structure_analyzer.compute_slide_similarity(slides)
        graph = self.graph_builder.build(slides, sections, similarities)
        
        # Expand with images
        if any(len(s.images) > 0 for s in slides):
            graph = self.graph_builder.expand_with_images(graph, slides)
        
        logger.info(f"✓ Built graph with {len(graph.nodes)} nodes")
        
        # Stage 4: Extract metadata
        logger.info("Stage 4: Extracting metadata...")
        self.metadata_extractor.batch_extract_metadata(slides)
        
        for section in sections:
            self.metadata_extractor.extract_section_metadata(section, slides)
        
        logger.info("✓ Metadata extracted")
        
        # Stage 5: Build index
        logger.info("Stage 5: Building index...")
        index = self.index_builder.build(
            document_id=document_id,
            document_title=document_title,
            document_path=pptx_path,
            slides=slides,
            sections=sections,
            graph=graph,
        )
        logger.info("✓ Index built")
        
        # Export if output directory specified
        if output_dir:
            self._export_results(index, graph, output_dir)
        
        logger.info(f"✓ Indexing complete! Generated DocumentIndex with {len(index.slides)} slides")
        return index
    
    def _export_results(
        self,
        index: DocumentIndex,
        graph,
        output_dir: str,
    ) -> None:
        """Export index and graph to files."""
        
        logger.info(f"Exporting results to {output_dir}")
        
        # Export index
        index_path = f"{output_dir}/index.json"
        self.index_builder.export_index(index, index_path, format="json")
        
        # Export graph
        graph_path = f"{output_dir}/graph.json"
        self.index_builder.export_graph(graph, graph_path)
        
        logger.info(f"✓ Exported to {output_dir}")
    
    def update_plugins(
        self,
        llm: Optional[BaseLLM] = None,
        embedder: Optional[BaseEmbedder] = None,
        vector_store: Optional[BaseVectorStore] = None,
    ) -> None:
        """Update plugins after initialization."""
        if llm:
            self.plugins.llm = llm
            self.metadata_extractor = MetadataExtractor(llm)
        
        if embedder:
            self.plugins.embedder = embedder
        
        if vector_store:
            self.plugins.vector_store = vector_store
        
        logger.info("Plugins updated")
