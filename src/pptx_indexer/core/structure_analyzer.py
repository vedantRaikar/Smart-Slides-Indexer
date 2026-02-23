"""Structure Analyzer - Dynamically determines slide hierarchy and semantic relationships.
Key component for intelligent slide organization.
"""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from ..schemas.slide_node import SectionNode, SlideNode

logger = logging.getLogger(__name__)


class StructureAnalyzer:
    """Analyzes slide presentation to determine:
    - Hierarchical sections
    - Topic boundaries
    - Semantic relationships
    - Slide grouping
    """

    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold

    def analyze(
        self, slides: List[SlideNode]
    ) -> Tuple[List[SectionNode], Dict[str, List[str]]]:
        """Analyze slides to create section hierarchy.

        Returns:
            (sections, slide_to_section_mapping)

        """
        logger.info(f"Analyzing structure of {len(slides)} slides")

        # Detect sections and hierarchies
        sections = self._detect_sections(slides)

        # Assign slides to sections
        slide_to_section = self._assign_slides_to_sections(slides, sections)

        # Build relationships within sections
        self._build_section_relationships(slides, sections, slide_to_section)

        logger.info(f"Detected {len(sections)} sections")
        return sections, slide_to_section

    def _detect_sections(self, slides: List[SlideNode]) -> List[SectionNode]:
        """Detect section boundaries using multiple heuristics."""
        sections = []
        current_section = None

        for i, slide in enumerate(slides):
            # Heuristic 1: Detect section breaks via title patterns
            is_section_title = self._is_section_title(slide)

            if is_section_title:
                # Save previous section
                if current_section:
                    sections.append(current_section)

                # Create new section
                current_section = SectionNode(
                    title=slide.title,
                    description=slide.subtitle or "",
                    slide_ids=[slide.slide_id],
                    topic=self._extract_topic(slide.title),
                )
                logger.debug(f"Detected section: {slide.title}")

            elif current_section:
                current_section.slide_ids.append(slide.slide_id)
            else:
                # No section detected yet, create default
                current_section = SectionNode(
                    title="Introduction",
                    slide_ids=[slide.slide_id],
                    topic="Introduction",
                )

        # Add final section
        if current_section and current_section.slide_ids:
            sections.append(current_section)

        return sections

    def _is_section_title(self, slide: SlideNode) -> bool:
        """Detect if slide is a section title."""
        # Heuristic 1: Few bullets (0-2)
        if len(slide.bullets) > 2:
            return False

        # Heuristic 2: Large title font (implied by no content)
        if not slide.bullets and slide.title and not slide.notes:
            return True

        # Heuristic 3: Matches pattern like "Part X", "Chapter Y", "Section Z"
        title_patterns = r"\b(part|chapter|section|unit|module|lesson|week|day)\s*\d*\b"
        if re.search(title_patterns, slide.title, re.IGNORECASE):
            return True

        # Heuristic 4: Has subtitle (cover slide pattern)
        if slide.subtitle and not slide.bullets:
            return True

        return False

    def _extract_topic(self, title: str) -> str:
        """Extract topic from title."""
        # Remove common prefixes
        title = re.sub(
            r"^(part|chapter|section|lesson|unit|module)\s*\d*\s*[-:]*\s*",
            "",
            title,
            flags=re.IGNORECASE,
        )
        return title.strip()

    def _assign_slides_to_sections(
        self,
        slides: List[SlideNode],
        sections: List[SectionNode],
    ) -> Dict[str, str]:
        """Map each slide to a section.
        Returns dict of slide_id -> section_id
        """
        mapping = {}

        for section in sections:
            for slide_id in section.slide_ids:
                mapping[slide_id] = section.section_id

        return mapping

    def _build_section_relationships(
        self,
        slides: List[SlideNode],
        sections: List[SectionNode],
        slide_to_section: Dict[str, str],
    ) -> None:
        """Build hierarchical relationships within and between sections."""
        # Create slide lookup
        slide_map = {s.slide_id: s for s in slides}

        # Build subtopics within sections
        for section in sections:
            subtopics = set()

            for slide_id in section.slide_ids:
                slide = slide_map.get(slide_id)
                if slide:
                    subtopics.update(slide.topics)

            section.subtopics = list(subtopics)

    def detect_topics(self, slides: List[SlideNode]) -> Dict[str, List[str]]:
        """Detect main topics and subtopics across slides.
        Returns mapping of topic -> slide_ids
        """
        topics = defaultdict(list)

        for slide in slides:
            # Extract topics from title
            title_topics = self._extract_topics_from_text(slide.title)

            for topic in title_topics:
                topics[topic].append(slide.slide_id)

            # Use predefined topics if available
            for topic in slide.topics:
                topics[topic].append(slide.slide_id)

        return dict(topics)

    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract potential topics from text using NLP heuristics."""
        topics = []

        # Split on common delimiters
        parts = re.split(r"[-:•]", text)

        for part in parts:
            part = part.strip()
            # Filter out very short parts
            if len(part.split()) >= 2 and len(part) > 5:
                topics.append(part)

        return topics

    def detect_repeated_themes(self, slides: List[SlideNode]) -> Dict[str, List[str]]:
        """Detect repeated themes/keywords across slides.
        Returns mapping of theme -> slide_ids
        """
        keyword_slides = defaultdict(list)

        for slide in slides:
            # Get all keywords from bullets
            for bullet in slide.bullets:
                words = bullet.text.lower().split()

                for word in words:
                    # Filter stop words and short words
                    if len(word) > 3 and word not in self._get_stop_words():
                        keyword_slides[word].append(slide.slide_id)

        # Filter to only repeated themes (appear in 3+ slides)
        repeated = {
            theme: slides
            for theme, slides in keyword_slides.items()
            if len(slides) >= 3
        }

        return repeated

    @staticmethod
    def _get_stop_words() -> Set[str]:
        """Common English stop words to filter."""
        return {
            "the",
            "and",
            "or",
            "a",
            "an",
            "to",
            "in",
            "is",
            "be",
            "at",
            "this",
            "that",
            "with",
            "for",
            "from",
            "by",
            "on",
            "can",
            "will",
            "was",
            "are",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "as",
            "of",
            "if",
            "about",
            "what",
            "which",
            "who",
            "when",
            "how",
            "why",
            "more",
            "most",
            "no",
            "not",
            "also",
        }

    def compute_slide_similarity(
        self,
        slides: List[SlideNode],
        embeddings: Optional[Dict[str, List[float]]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Compute similarity matrix between slides.
        Can use embeddings if provided, otherwise fallback to keyword overlap.
        """
        if embeddings:
            # Use embeddings for similarity
            return self._compute_embedding_similarity(embeddings)
        else:
            # Use keyword overlap
            return self._compute_keyword_similarity(slides)

    def _compute_keyword_similarity(
        self, slides: List[SlideNode]
    ) -> Dict[str, Dict[str, float]]:
        """Compute similarity based on keyword overlap."""
        similarities = {}

        for i, slide1 in enumerate(slides):
            slide1_keywords = set(slide1.keywords) | set(slide1.topics)
            similarities[slide1.slide_id] = {}

            for slide2 in slides[i + 1 :]:
                slide2_keywords = set(slide2.keywords) | set(slide2.topics)

                # Jaccard similarity
                if not slide1_keywords and not slide2_keywords:
                    sim = 1.0
                else:
                    intersection = len(slide1_keywords & slide2_keywords)
                    union = len(slide1_keywords | slide2_keywords)
                    sim = intersection / union if union > 0 else 0.0

                similarities[slide1.slide_id][slide2.slide_id] = sim

                # Make symmetric
                if slide2.slide_id not in similarities:
                    similarities[slide2.slide_id] = {}
                similarities[slide2.slide_id][slide1.slide_id] = sim

        return similarities

    def _compute_embedding_similarity(
        self,
        embeddings: Dict[str, List[float]],
    ) -> Dict[str, Dict[str, float]]:
        """Compute similarity from embeddings using cosine distance."""
        from math import sqrt

        similarities = {}
        slide_ids = list(embeddings.keys())

        for i, id1 in enumerate(slide_ids):
            similarities[id1] = {}
            vec1 = embeddings[id1]

            for id2 in slide_ids[i + 1 :]:
                vec2 = embeddings[id2]

                # Cosine similarity
                dot_product = sum(a * b for a, b in zip(vec1, vec2))
                mag1 = sqrt(sum(a * a for a in vec1))
                mag2 = sqrt(sum(b * b for b in vec2))

                sim = dot_product / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0.0
                similarities[id1][id2] = sim

                if id2 not in similarities:
                    similarities[id2] = {}
                similarities[id2][id1] = sim

        return similarities

    def identify_transitions(self, slides: List[SlideNode]) -> List[Tuple[int, str]]:
        """Identify structural transitions between slides.
        Returns list of (slide_index, transition_type)
        """
        transitions = []

        for i in range(1, len(slides)):
            prev_slide = slides[i - 1]
            curr_slide = slides[i]

            transition = self._detect_transition(prev_slide, curr_slide)
            if transition:
                transitions.append((i, transition))

        return transitions

    def _detect_transition(
        self, prev_slide: SlideNode, curr_slide: SlideNode
    ) -> Optional[str]:
        """Detect transition type between slides."""
        # Transition to section title
        if self._is_section_title(curr_slide):
            return "section_break"

        # Return from section title
        if self._is_section_title(prev_slide) and not self._is_section_title(
            curr_slide
        ):
            return "section_start"

        # Conclusion slides
        if any(
            word in curr_slide.title.lower()
            for word in ["conclusion", "summary", "recap"]
        ):
            return "conclusion"

        return None
