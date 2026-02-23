"""Slide node schema for PPTX indexer.
Represents atomic units within the document structure.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    """Types of nodes in the slide graph."""

    SLIDE = "slide"
    SECTION = "section"
    CONCEPT = "concept"
    IMAGE = "image"
    TABLE = "table"
    SPEAKER_NOTE = "speaker_note"


class ContentType(str, Enum):
    """Types of content within a slide."""

    TITLE = "title"
    BULLET = "bullet"
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    SHAPE = "shape"


@dataclass
class BulletPoint:
    """Represents a bullet point in a slide."""

    text: str
    level: int  # Hierarchy level (0=root, 1=sub, etc)
    index: int
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "level": self.level,
            "index": self.index,
            "keywords": self.keywords,
        }


@dataclass
class ImageNode:
    """Represents an image within a slide."""

    image_id: str
    image_path: str
    caption: Optional[str] = None
    ocr_text: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_id": self.image_id,
            "image_path": self.image_path,
            "caption": self.caption,
            "ocr_text": self.ocr_text,
            "keywords": self.keywords,
        }


@dataclass
class TableNode:
    """Represents a table within a slide."""

    table_id: str
    headers: List[str]
    rows: List[List[str]]
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_id": self.table_id,
            "headers": self.headers,
            "rows": self.rows,
            "summary": self.summary,
            "keywords": self.keywords,
        }


@dataclass
class SlideNode:
    """Represents a single slide in the presentation.
    This is the primary indexing unit.
    """

    # Identifiers
    slide_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    slide_number: int = 0

    # Content
    title: str = ""
    subtitle: Optional[str] = None
    bullets: List[BulletPoint] = field(default_factory=list)
    images: List[ImageNode] = field(default_factory=list)
    tables: List[TableNode] = field(default_factory=list)
    notes: Optional[str] = None

    # Structure
    layout_type: str = "default"  # e.g., "title_slide", "bullet_slide", "blank"
    section_id: Optional[str] = None  # Reference to parent section

    # Metadata
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    learning_objectives: List[str] = field(default_factory=list)

    # Embeddings
    embedding: Optional[List[float]] = None
    title_embedding: Optional[List[float]] = None
    content_embedding: Optional[List[float]] = None

    # Metrics
    importance_score: float = 0.5  # 0-1 range
    complexity_score: float = 0.5  # 0-1 range

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Relationships
    next_slide_id: Optional[str] = None
    prev_slide_id: Optional[str] = None
    references: List[str] = field(default_factory=list)  # Slide IDs referenced
    similar_slides: List[tuple[str, float]] = field(
        default_factory=list
    )  # (slide_id, similarity)

    def get_full_text(self) -> str:
        """Get all textual content from the slide."""
        parts = [self.title]

        if self.subtitle:
            parts.append(self.subtitle)

        for bullet in self.bullets:
            parts.append(bullet.text)

        for table in self.tables:
            parts.extend(table.headers)
            for row in table.rows:
                parts.extend(row)

        if self.notes:
            parts.append(self.notes)

        return " ".join(filter(None, parts))

    def get_rich_text_hierarchy(self) -> str:
        """Get rich text representation preserving hierarchy."""
        parts = [f"# {self.title}"]

        if self.subtitle:
            parts.append(f"## {self.subtitle}")

        current_level = -1
        for bullet in self.bullets:
            indent = "  " * bullet.level
            if bullet.level > current_level:
                parts.append(f"{indent}- {bullet.text}")
            else:
                parts.append(f"{indent}- {bullet.text}")
            current_level = bullet.level

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert slide to dictionary."""
        return {
            "slide_id": self.slide_id,
            "slide_number": self.slide_number,
            "title": self.title,
            "subtitle": self.subtitle,
            "bullets": [b.to_dict() for b in self.bullets],
            "images": [img.to_dict() for img in self.images],
            "tables": [t.to_dict() for t in self.tables],
            "notes": self.notes,
            "layout_type": self.layout_type,
            "section_id": self.section_id,
            "keywords": self.keywords,
            "topics": self.topics,
            "summary": self.summary,
            "learning_objectives": self.learning_objectives,
            "importance_score": self.importance_score,
            "complexity_score": self.complexity_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SectionNode:
    """Represents a section grouping multiple slides.
    Used for hierarchical organization.
    """

    section_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: Optional[str] = None

    slide_ids: List[str] = field(default_factory=list)
    topic: str = ""
    subtopics: List[str] = field(default_factory=list)

    keywords: List[str] = field(default_factory=list)
    summary: Optional[str] = None

    # Hierarchy
    parent_section_id: Optional[str] = None
    subsection_ids: List[str] = field(default_factory=list)

    # Embedding
    embedding: Optional[List[float]] = None

    # Metrics
    importance_score: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "description": self.description,
            "slide_ids": self.slide_ids,
            "topic": self.topic,
            "subtopics": self.subtopics,
            "keywords": self.keywords,
            "summary": self.summary,
        }
