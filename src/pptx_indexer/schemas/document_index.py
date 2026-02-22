"""Document index schema - complete indexed representation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .slide_graph_schema import SlideGraph
from .slide_node import SectionNode, SlideNode


@dataclass
class DocumentStats:
    """Statistics about the indexed document."""

    total_slides: int = 0
    total_sections: int = 0
    total_images: int = 0
    total_tables: int = 0
    average_slide_complexity: float = 0.0
    total_words: int = 0
    estimated_reading_time_minutes: int = 0


@dataclass
class DocumentIndex:
    """Complete hierarchical index of a PowerPoint document.
    This is the output of the indexing pipeline.
    """

    # Document metadata
    document_id: str
    document_title: str
    document_path: str

    # Index components
    slides: Dict[str, SlideNode] = field(default_factory=dict)
    sections: Dict[str, SectionNode] = field(default_factory=dict)
    graph: Optional[SlideGraph] = None

    # Multi-resolution indexing
    slide_embeddings: Dict[str, List[float]] = field(default_factory=dict)
    section_embeddings: Dict[str, List[float]] = field(default_factory=dict)
    document_embedding: Optional[List[float]] = None

    # Keyword indices
    keyword_to_slides: Dict[str, List[str]] = field(default_factory=dict)
    topic_to_slides: Dict[str, List[str]] = field(default_factory=dict)
    concept_to_slides: Dict[str, List[str]] = field(default_factory=dict)

    # Cross-references
    image_references: Dict[str, str] = field(default_factory=dict)  # image_id -> slide_id
    external_references: Dict[str, str] = field(default_factory=dict)

    # Similarity matrices
    slide_similarity_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    concept_clusters: Dict[int, List[str]] = field(default_factory=dict)  # cluster_id -> slide_ids

    # Statistics
    stats: DocumentStats = field(default_factory=DocumentStats)

    # Timeline
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    indexed_version: str = "1.0"

    def add_slide(self, slide: SlideNode) -> None:
        """Add a slide to the index."""
        self.slides[slide.slide_id] = slide
        self.stats.total_slides += 1

    def add_section(self, section: SectionNode) -> None:
        """Add a section to the index."""
        self.sections[section.section_id] = section
        self.stats.total_sections += 1

    def get_slide(self, slide_id: str) -> Optional[SlideNode]:
        """Retrieve a slide by ID."""
        return self.slides.get(slide_id)

    def get_section(self, section_id: str) -> Optional[SectionNode]:
        """Retrieve a section by ID."""
        return self.sections.get(section_id)

    def get_slides_by_keyword(self, keyword: str) -> List[SlideNode]:
        """Get all slides containing a keyword."""
        slide_ids = self.keyword_to_slides.get(keyword.lower(), [])
        return [self.slides[sid] for sid in slide_ids if sid in self.slides]

    def get_slides_by_topic(self, topic: str) -> List[SlideNode]:
        """Get all slides about a topic."""
        slide_ids = self.topic_to_slides.get(topic.lower(), [])
        return [self.slides[sid] for sid in slide_ids if sid in self.slides]

    def get_concept_cluster(self, cluster_id: int) -> List[SlideNode]:
        """Get slides in a concept cluster."""
        slide_ids = self.concept_clusters.get(cluster_id, [])
        return [self.slides[sid] for sid in slide_ids if sid in self.slides]

    def build_keyword_index(self) -> None:
        """Rebuild keyword index from slides."""
        self.keyword_to_slides.clear()

        for slide_id, slide in self.slides.items():
            for keyword in slide.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in self.keyword_to_slides:
                    self.keyword_to_slides[keyword_lower] = []
                self.keyword_to_slides[keyword_lower].append(slide_id)

    def build_topic_index(self) -> None:
        """Rebuild topic index from slides."""
        self.topic_to_slides.clear()

        for slide_id, slide in self.slides.items():
            for topic in slide.topics:
                topic_lower = topic.lower()
                if topic_lower not in self.topic_to_slides:
                    self.topic_to_slides[topic_lower] = []
                self.topic_to_slides[topic_lower].append(slide_id)

    def to_dict(self) -> Dict[str, Any]:
        """Export index to dictionary."""
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "stats": {
                "total_slides": self.stats.total_slides,
                "total_sections": self.stats.total_sections,
                "total_images": self.stats.total_images,
                "total_keywords": len(self.keyword_to_slides),
                "total_topics": len(self.topic_to_slides),
            },
            "slides": {sid: slide.to_dict() for sid, slide in self.slides.items()},
            "sections": {sid: section.to_dict() for sid, section in self.sections.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_json(self) -> str:
        """Export index to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2, default=str)
