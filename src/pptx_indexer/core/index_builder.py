"""Index Builder - Constructs complete hierarchical index.
Handles embeddings, vector storage, graph persistence.
"""

import json
import logging
from typing import List, Optional

from ..plugins.base_llm import (
    BaseEmbedder,
    BaseImageCaptioner,
    BaseOCR,
    BaseVectorStore,
)
from ..schemas.document_index import DocumentIndex
from ..schemas.slide_graph_schema import SlideGraph
from ..schemas.slide_node import SectionNode, SlideNode

logger = logging.getLogger(__name__)


class IndexBuilder:
    """Builds complete document index.
    - Manages embeddings
    - Stores vectors
    - Persists graph
    - Exports multi-format output
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: Optional[BaseVectorStore] = None,
        ocr: Optional[BaseOCR] = None,
        image_captioner: Optional[BaseImageCaptioner] = None,
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.ocr = ocr
        self.image_captioner = image_captioner

    def build(
        self,
        document_id: str,
        document_title: str,
        document_path: str,
        slides: List[SlideNode],
        sections: List[SectionNode],
        graph: SlideGraph,
    ) -> DocumentIndex:
        """Build complete document index."""
        logger.info(f"Building index for: {document_title}")

        index = DocumentIndex(
            document_id=document_id,
            document_title=document_title,
            document_path=document_path,
        )

        # Add slides and sections
        for slide in slides:
            index.add_slide(slide)

        for section in sections:
            index.add_section(section)

        index.graph = graph

        # Generate embeddings
        logger.info("Generating embeddings...")
        self._generate_embeddings(index)

        # Store vectors in vector store
        if self.vector_store:
            logger.info("Storing vectors...")
            self._store_vectors(index)

        # Build search indices
        logger.info("Building search indices...")
        index.build_keyword_index()
        index.build_topic_index()

        # Compute statistics
        logger.info("Computing statistics...")
        self._compute_statistics(index, slides)

        # Extract image metadata
        if self.image_captioner or self.ocr:
            logger.info("Processing images...")
            self._process_images(index, slides)

        logger.info(f"Index built successfully with {len(index.slides)} slides")
        return index

    def _generate_embeddings(self, index: DocumentIndex) -> None:
        """Generate embeddings for all content."""
        # Slide embeddings
        slide_texts = [s.get_full_text() for s in index.slides.values()]
        slide_embeddings = self.embedder.batch_embed(slide_texts)

        for (slide_id, slide), embedding in zip(index.slides.items(), slide_embeddings):
            slide.embedding = embedding
            index.slide_embeddings[slide_id] = embedding

        # Title embeddings
        title_texts = [s.title for s in index.slides.values()]
        title_embeddings = self.embedder.batch_embed(title_texts)

        for (slide_id, slide), embedding in zip(index.slides.items(), title_embeddings):
            slide.title_embedding = embedding

        # Section embeddings
        section_texts = [s.title for s in index.sections.values()]
        if section_texts:
            section_embeddings = self.embedder.batch_embed(section_texts)

            for (section_id, section), embedding in zip(
                index.sections.items(), section_embeddings
            ):
                section.embedding = embedding
                index.section_embeddings[section_id] = embedding

        # Document embedding (mean of all slide embeddings)
        if slide_embeddings:
            import numpy as np

            doc_embedding = np.mean(slide_embeddings, axis=0).tolist()
            index.document_embedding = doc_embedding

        logger.debug(f"Generated embeddings for {len(slide_embeddings)} slides")

    def _store_vectors(self, index: DocumentIndex) -> None:
        """Store embeddings in vector store."""
        if not self.vector_store:
            return

        # Store slide embeddings
        slide_ids = list(index.slide_embeddings.keys())
        slide_vecs = [index.slide_embeddings[sid] for sid in slide_ids]
        slide_metadata = [
            {
                "type": "slide",
                "title": index.slides[sid].title,
                "section_id": index.slides[sid].section_id,
            }
            for sid in slide_ids
        ]

        self.vector_store.add(slide_ids, slide_vecs, slide_metadata)

        # Store section embeddings
        section_ids = list(index.section_embeddings.keys())
        if section_ids:
            section_vecs = [index.section_embeddings[sid] for sid in section_ids]
            section_metadata = [
                {
                    "type": "section",
                    "title": index.sections[sid].title,
                    "slide_count": len(index.sections[sid].slide_ids),
                }
                for sid in section_ids
            ]

            self.vector_store.add(section_ids, section_vecs, section_metadata)

        logger.debug(f"Stored {len(slide_ids) + len(section_ids)} vectors")

    def _compute_statistics(
        self, index: DocumentIndex, slides: List[SlideNode]
    ) -> None:
        """Compute document statistics."""
        stats = index.stats
        stats.total_slides = len(index.slides)
        stats.total_sections = len(index.sections)

        total_images = sum(len(s.images) for s in slides)
        stats.total_images = total_images

        total_tables = sum(len(s.tables) for s in slides)
        stats.total_tables += total_tables

        # Count words
        total_words = sum(len(s.get_full_text().split()) for s in slides)
        stats.total_words = total_words

        # Estimate reading time (200 words per minute)
        stats.estimated_reading_time_minutes = max(1, total_words // 200)

        # Average complexity
        if slides:
            avg_complexity = sum(s.complexity_score for s in slides) / len(slides)
            stats.average_slide_complexity = avg_complexity

    def _process_images(self, index: DocumentIndex, slides: List[SlideNode]) -> None:
        """Process images: OCR and captions."""
        for slide in slides:
            for image in slide.images:
                # OCR
                if self.ocr:
                    try:
                        ocr_text = self.ocr.extract_text(image.image_path)
                        image.ocr_text = ocr_text
                        logger.debug(
                            f"OCR for image {image.image_id}: {len(ocr_text)} chars"
                        )
                    except Exception as e:
                        logger.warning(f"OCR failed for {image.image_path}: {e}")

                # Caption
                if self.image_captioner:
                    try:
                        caption = self.image_captioner.caption(image.image_path)
                        image.caption = caption
                        logger.debug(f"Captioned image {image.image_id}")
                    except Exception as e:
                        logger.warning(f"Captioning failed for {image.image_path}: {e}")

                # Embed image text
                image_text = f"{image.caption} {image.ocr_text}".strip()
                if image_text:
                    embedding = self.embedder.embed(image_text)
                    image.embedding = embedding

                # Track image reference
                index.image_references[image.image_id] = slide.slide_id

    def export_index(
        self,
        index: DocumentIndex,
        output_path: str,
        format: str = "json",
    ) -> None:
        """Export index to file.

        Args:
            index: DocumentIndex to export
            output_path: Output file path
            format: Export format (json, jsonl, pickle)

        """
        logger.info(f"Exporting index to {format}: {output_path}")

        if format == "json":
            self._export_json(index, output_path)
        elif format == "jsonl":
            self._export_jsonl(index, output_path)
        elif format == "pickle":
            self._export_pickle(index, output_path)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _export_json(self, index: DocumentIndex, output_path: str) -> None:
        """Export as JSON."""
        with open(output_path, "w") as f:
            f.write(index.to_json())
        logger.info(f"Exported to JSON: {output_path}")

    def _export_jsonl(self, index: DocumentIndex, output_path: str) -> None:
        """Export as JSONL (one object per line)."""
        import json

        with open(output_path, "w") as f:
            # Write metadata
            metadata = {
                "type": "metadata",
                "document_id": index.document_id,
                "document_title": index.document_title,
                "slide_count": len(index.slides),
                "section_count": len(index.sections),
            }
            f.write(json.dumps(metadata) + "\n")

            # Write each slide
            for slide in index.slides.values():
                f.write(json.dumps(slide.to_dict()) + "\n")

            # Write each section
            for section in index.sections.values():
                f.write(json.dumps(section.to_dict()) + "\n")

        logger.info(f"Exported to JSONL: {output_path}")

    def _export_pickle(self, index: DocumentIndex, output_path: str) -> None:
        """Export as pickle (Python serialization)."""
        import pickle

        with open(output_path, "wb") as f:
            pickle.dump(index, f)
        logger.info(f"Exported to pickle: {output_path}")

    def export_graph(self, graph: SlideGraph, output_path: str) -> None:
        """Export graph structure."""
        graph_dict = graph.to_dict()

        with open(output_path, "w") as f:
            json.dump(graph_dict, f, indent=2, default=str)

        logger.info(f"Exported graph to {output_path}")
