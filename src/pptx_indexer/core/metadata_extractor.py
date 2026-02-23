"""Metadata Extractor - Extracts semantic metadata from slides using LLM.
Includes keywords, topics, summaries, learning objectives.
"""

import json
import logging
from typing import Dict, List, Optional

from ..plugins.base_llm import BaseLLM
from ..schemas.slide_node import SectionNode, SlideNode

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts rich metadata from slides using LLM.
    Enables semantic understanding and better retrieval.
    """

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def extract_slide_metadata(self, slide: SlideNode) -> None:
        """Extract and populate metadata for a single slide.
        Modifies slide in-place.
        """
        try:
            # Get full text
            content = slide.get_full_text()

            if not content.strip():
                logger.warning(f"Skipping empty slide {slide.slide_id}")
                return

            # Extract keywords
            keywords = self._extract_keywords(content)
            slide.keywords = keywords

            # Extract topics
            topics = self._extract_topics(slide.title, content)
            slide.topics = topics

            # Generate summary
            summary = self._generate_summary(slide.title, content)
            slide.summary = summary

            # Extract learning objectives (if educational)
            objectives = self._extract_learning_objectives(content)
            slide.learning_objectives = objectives

            logger.debug(f"Extracted metadata for slide: {slide.title[:30]}")

        except Exception as e:
            logger.error(f"Failed to extract metadata for slide {slide.slide_id}: {e}")

    def extract_section_metadata(
        self, section: SectionNode, slides: List[SlideNode]
    ) -> None:
        """Extract metadata for a section."""
        try:
            # Collect content from all slides in section
            section_content = section.title + "\n"
            section_content += section.description + "\n"

            for slide_id in section.slide_ids:
                for slide in slides:
                    if slide.slide_id == slide_id:
                        section_content += slide.get_full_text() + "\n"
                        break

            # Extract topics and keywords
            topics = self._extract_topics_batch([section.title], section_content)
            section.subtopics = topics

            keywords = self._extract_keywords(section_content, top_k=15)
            section.keywords = keywords

            # Generate summary
            summary = self._generate_summary(section.title, section_content)
            section.summary = summary

            logger.debug(f"Extracted metadata for section: {section.title}")

        except Exception as e:
            logger.error(f"Failed to extract section metadata: {e}")

    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """Extract important keywords from text using LLM."""
        prompt = f"""Extract the {top_k} most important keywords from this text. 
        Return ONLY a JSON array of strings, nothing else.
        
        Text:
        {text[:1500]}
        
        JSON array:"""

        try:
            response = self.llm.generate(prompt, temperature=0.1)
            keywords = json.loads(response)
            return keywords[:top_k] if isinstance(keywords, list) else []
        except Exception as e:
            logger.warning(f"Failed to extract keywords: {e}")
            return []

    def _extract_topics(self, title: str, content: str) -> List[str]:
        """Extract main topics from slide."""
        prompt = f"""Identify 3-5 main topics/themes from this slide. Return as JSON array.
        
        Title: {title}
        Content: {content[:1000]}
        
        JSON array of topics:"""

        try:
            response = self.llm.generate(prompt, temperature=0.1)
            topics = json.loads(response)
            return topics[:5] if isinstance(topics, list) else []
        except Exception as e:
            logger.warning(f"Failed to extract topics: {e}")
            return []

    def _extract_topics_batch(self, titles: List[str], content: str) -> List[str]:
        """Extract topics for multiple items."""
        topics_set = set()

        for title in titles:
            topics = self._extract_topics(title, content)
            topics_set.update(topics)

        return list(topics_set)[:10]

    def _generate_summary(self, title: str, content: str, max_length: int = 150) -> str:
        """Generate concise summary of slide content."""
        prompt = f"""Write a concise {max_length}-character summary of this slide content.
        Make it informative and suitable for indexing/search.
        
        Title: {title}
        Content: {content[:1500]}
        
        Summary:"""

        try:
            summary = self.llm.generate(prompt, temperature=0.3, max_tokens=100)
            return summary.strip()[:max_length]
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}")
            return content[:max_length]

    def _extract_learning_objectives(self, content: str) -> List[str]:
        """Extract learning objectives if this is educational content."""
        prompt = (
            """Extract 2-4 learning objectives from this slide content.
        Return as JSON array. Return empty array if not educational.
        
        Content:
        """
            + content[:1000]
            + """
        
        JSON array:"""
        )

        try:
            response = self.llm.generate(prompt, temperature=0.1)
            objectives = json.loads(response)
            return objectives[:4] if isinstance(objectives, list) else []
        except Exception as e:
            logger.warning(f"Failed to extract learning objectives: {e}")
            return []

    def extract_image_metadata(
        self,
        slide: SlideNode,
        ocr_texts: Optional[Dict[str, str]] = None,
    ) -> None:
        """Extract captions and keywords for images.

        Args:
            slide: Slide containing images
            ocr_texts: Optional OCR results for images (image_id -> text)

        """
        for image in slide.images:
            # Use OCR text if available
            if ocr_texts and image.image_id in ocr_texts:
                image.ocr_text = ocr_texts[image.image_id]

            # Extract keywords from caption or OCR
            text_source = image.caption or image.ocr_text or ""
            if text_source:
                keywords = self._extract_keywords(text_source, top_k=5)
                image.keywords = keywords

    @staticmethod
    def extract_named_entities(text: str) -> List[Dict[str, str]]:
        """Extract named entities (people, places, organizations, etc).
        Uses simple pattern matching (can be extended with NER model).
        """
        # Simple pattern matching for common entity types
        import re

        entities = []

        # Capital word sequences (potential entities)
        pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
        matches = re.finditer(pattern, text)

        for match in matches:
            entity = match.group()
            if len(entity) > 2:
                entities.append(
                    {
                        "text": entity,
                        "type": "PERSON_OR_ORG",  # Could be refined
                        "offset": match.start(),
                    }
                )

        # Remove duplicates
        unique_entities = {e["text"]: e for e in entities}
        return list(unique_entities.values())

    def batch_extract_metadata(self, slides: List[SlideNode]) -> None:
        """Extract metadata for multiple slides."""
        logger.info(f"Extracting metadata for {len(slides)} slides")

        for slide in slides:
            self._extract_slide_metadata_safe(slide)

        logger.info("Metadata extraction complete")

    def _extract_slide_metadata_safe(self, slide: SlideNode) -> None:
        """Safely extract metadata with error handling."""
        try:
            self.extract_slide_metadata(slide)
        except Exception as e:
            logger.warning(
                f"Skipped metadata extraction for slide {slide.slide_id}: {e}"
            )
