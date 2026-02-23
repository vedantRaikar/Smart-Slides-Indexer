"""Extended tests for core modules to improve coverage."""

import os
from unittest.mock import Mock, patch

import pytest


class TestIndexBuilderExtended:
    """Extended tests for IndexBuilder."""

    def test_build_complete_index(self, temp_dir):
        """Test building a complete index."""
        from pptx_indexer.core.index_builder import IndexBuilder
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint, SectionNode
        from pptx_indexer.schemas.slide_graph_schema import SlideGraph

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Introduction",
                bullets=[BulletPoint(text="Welcome", level=0, index=0)],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Main Content",
                bullets=[BulletPoint(text="Point 1", level=0, index=0)],
            ),
        ]

        mock_embedder = Mock()
        mock_embedder.batch_embed.side_effect = lambda texts: [[0.1] * 384] * len(texts)
        mock_embedder.embed.return_value = [0.1] * 384

        mock_vector_store = Mock()

        builder = IndexBuilder(
            embedder=mock_embedder,
            vector_store=mock_vector_store,
        )

        sections = [
            SectionNode(title="Introduction", slide_ids=["slide_1"]),
            SectionNode(title="Main", slide_ids=["slide_2"]),
        ]
        graph = SlideGraph()

        index = builder.build(
            document_id="doc1",
            document_title="Test Document",
            document_path="/test.pptx",
            slides=slides,
            sections=sections,
            graph=graph,
        )

        assert index.document_id == "doc1"
        assert len(index.slides) == 2
        assert len(index.sections) == 2

    def test_build_without_vector_store(self, temp_dir):
        """Test building index without vector store."""
        from pptx_indexer.core.index_builder import IndexBuilder
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint
        from pptx_indexer.schemas.slide_graph_schema import SlideGraph

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Test",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
        ]

        mock_embedder = Mock()
        mock_embedder.batch_embed.side_effect = lambda texts: [[0.1] * 384] * len(texts)

        builder = IndexBuilder(embedder=mock_embedder)

        index = builder.build(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
            slides=slides,
            sections=[],
            graph=SlideGraph(),
        )

        assert index.document_embedding is not None

    def test_build_with_image_processing(self, temp_dir):
        """Test building index with image OCR and captioning."""
        from pptx_indexer.core.index_builder import IndexBuilder
        from pptx_indexer.schemas.slide_node import (
            SlideNode,
            BulletPoint,
            ImageNode,
        )
        from pptx_indexer.schemas.slide_graph_schema import SlideGraph

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Test",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
                images=[ImageNode(image_id="img1", image_path="/test.png")],
            ),
        ]

        mock_embedder = Mock()
        mock_embedder.batch_embed.side_effect = lambda texts: [[0.1] * 384] * len(texts)
        mock_embedder.embed.return_value = [0.1] * 384

        mock_ocr = Mock()
        mock_ocr.extract_text.return_value = "OCR extracted text"

        mock_captioner = Mock()
        mock_captioner.caption.return_value = "Image caption"

        builder = IndexBuilder(
            embedder=mock_embedder,
            ocr=mock_ocr,
            image_captioner=mock_captioner,
        )

        index = builder.build(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
            slides=slides,
            sections=[],
            graph=SlideGraph(),
        )

        assert len(index.image_references) > 0

    def test_export_index_json(self, temp_dir):
        """Test exporting index to JSON."""
        from pptx_indexer.core.index_builder import IndexBuilder
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint
        from pptx_indexer.schemas.document_index import DocumentIndex

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Test",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
        ]

        mock_embedder = Mock()
        mock_embedder.batch_embed.side_effect = lambda texts: [[0.1] * 384] * len(texts)

        builder = IndexBuilder(embedder=mock_embedder)

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        for slide in slides:
            index.add_slide(slide)

        output_path = os.path.join(temp_dir, "index.json")
        builder.export_index(index, output_path, format="json")

        assert os.path.exists(output_path)

    def test_export_index_jsonl(self, temp_dir):
        """Test exporting index to JSONL."""
        from pptx_indexer.core.index_builder import IndexBuilder
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint
        from pptx_indexer.schemas.document_index import DocumentIndex

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Test",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
        ]

        mock_embedder = Mock()
        mock_embedder.batch_embed.side_effect = lambda texts: [[0.1] * 384] * len(texts)

        builder = IndexBuilder(embedder=mock_embedder)

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        for slide in slides:
            index.add_slide(slide)

        output_path = os.path.join(temp_dir, "index.jsonl")
        builder.export_index(index, output_path, format="jsonl")

        assert os.path.exists(output_path)

    def test_export_index_pickle(self, temp_dir):
        """Test exporting index to pickle."""
        from pptx_indexer.core.index_builder import IndexBuilder
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint
        from pptx_indexer.schemas.document_index import DocumentIndex

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Test",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
        ]

        mock_embedder = Mock()
        mock_embedder.batch_embed.side_effect = lambda texts: [[0.1] * 384] * len(texts)

        builder = IndexBuilder(embedder=mock_embedder)

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        for slide in slides:
            index.add_slide(slide)

        output_path = os.path.join(temp_dir, "index.pkl")
        builder.export_index(index, output_path, format="pickle")

        assert os.path.exists(output_path)

    def test_export_index_invalid_format(self, temp_dir):
        """Test exporting with invalid format."""
        from pptx_indexer.core.index_builder import IndexBuilder
        from pptx_indexer.schemas.document_index import DocumentIndex

        mock_embedder = Mock()
        builder = IndexBuilder(embedder=mock_embedder)

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )

        with pytest.raises(ValueError):
            builder.export_index(
                index, os.path.join(temp_dir, "index.txt"), format="txt"
            )

    def test_export_graph(self, temp_dir):
        """Test exporting graph."""
        from pptx_indexer.core.index_builder import IndexBuilder
        from pptx_indexer.schemas.slide_graph_schema import SlideGraph, SlideGraphNode

        mock_embedder = Mock()
        builder = IndexBuilder(embedder=mock_embedder)

        graph = SlideGraph()
        graph.add_node(SlideGraphNode(node_id="slide_1", node_type="slide", content={}))

        output_path = os.path.join(temp_dir, "graph.json")
        builder.export_graph(graph, output_path)

        assert os.path.exists(output_path)


class TestMetadataExtractorExtended:
    """Extended tests for MetadataExtractor."""

    def test_extract_slide_metadata(self):
        """Test extracting metadata from a slide."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        mock_llm = Mock()
        mock_llm.generate.side_effect = [
            '["keyword1", "keyword2"]',
            '["topic1", "topic2"]',
            "This is a summary.",
            '["objective1", "objective2"]',
        ]

        extractor = MetadataExtractor(llm=mock_llm)

        slide = SlideNode(
            slide_number=1,
            slide_id="slide_1",
            title="Test Slide",
            bullets=[BulletPoint(text="Content", level=0, index=0)],
        )

        extractor.extract_slide_metadata(slide)

        assert len(slide.keywords) > 0
        assert len(slide.topics) > 0

    def test_extract_slide_metadata_empty_content(self):
        """Test extracting metadata from empty slide."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor
        from pptx_indexer.schemas.slide_node import SlideNode

        mock_llm = Mock()
        extractor = MetadataExtractor(llm=mock_llm)

        slide = SlideNode(slide_number=1, slide_id="slide_1")
        slide.bullets = []

        extractor.extract_slide_metadata(slide)

        mock_llm.generate.assert_not_called()

    def test_extract_slide_metadata_llm_error(self):
        """Test handling LLM errors during metadata extraction."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        mock_llm = Mock()
        mock_llm.generate.side_effect = Exception("LLM error")

        extractor = MetadataExtractor(llm=mock_llm)

        slide = SlideNode(
            slide_number=1,
            slide_id="slide_1",
            title="Test",
            bullets=[BulletPoint(text="Content", level=0, index=0)],
        )

        extractor.extract_slide_metadata(slide)

    def test_extract_section_metadata(self):
        """Test extracting section metadata."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor
        from pptx_indexer.schemas.slide_node import SectionNode, SlideNode, BulletPoint

        mock_llm = Mock()
        mock_llm.generate.side_effect = [
            '["topic1"]',
            '["keyword1", "keyword2"]',
            "Section summary",
        ]

        extractor = MetadataExtractor(llm=mock_llm)

        section = SectionNode(
            title="Test Section", slide_ids=["slide_1"], description="Test description"
        )
        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Slide 1",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
        ]

        extractor.extract_section_metadata(section, slides)

        assert section.summary is not None

    def test_extract_named_entities(self):
        """Test extracting named entities."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor

        text = "John Smith works at Google in New York."
        entities = MetadataExtractor.extract_named_entities(text)

        assert len(entities) > 0

    def test_batch_extract_metadata(self):
        """Test batch metadata extraction."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        mock_llm = Mock()
        mock_llm.generate.side_effect = [
            '["kw1"]',
            '["topic1"]',
            "summary",
            '["obj1"]',
        ]

        extractor = MetadataExtractor(llm=mock_llm)

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Slide 1",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
        ]

        extractor.batch_extract_metadata(slides)

    def test_extract_image_metadata(self):
        """Test extracting image metadata."""
        from pptx_indexer.core.metadata_extractor import MetadataExtractor
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint, ImageNode

        mock_llm = Mock()
        mock_llm.generate.return_value = '["img_keyword"]'

        extractor = MetadataExtractor(llm=mock_llm)

        slide = SlideNode(
            slide_number=1,
            slide_id="slide_1",
            title="Test",
            bullets=[BulletPoint(text="Content", level=0, index=0)],
        )
        slide.images = [
            ImageNode(image_id="img1", image_path="/test.png", caption="Test caption")
        ]

        extractor.extract_image_metadata(slide)


class TestStructureAnalyzerExtended:
    """Extended tests for StructureAnalyzer."""

    def test_analyze_slides(self):
        """Test analyzing slide structure."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Intro",
                bullets=[BulletPoint(text="Welcome", level=0, index=0)],
                keywords=["intro"],
                topics=["topic1"],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Content",
                bullets=[BulletPoint(text="Point", level=0, index=0)],
                keywords=["point"],
                topics=["topic1"],
            ),
        ]

        analyzer = StructureAnalyzer()
        sections, mapping = analyzer.analyze(slides)

        assert len(sections) > 0
        assert len(mapping) == len(slides)

    def test_detect_sections(self):
        """Test section detection."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Intro",
                bullets=[BulletPoint(text="Welcome", level=0, index=0)],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Content",
                bullets=[BulletPoint(text="Point", level=0, index=0)],
            ),
        ]

        analyzer = StructureAnalyzer()
        sections = analyzer._detect_sections(slides)

        assert len(sections) > 0

    def test_is_section_title(self):
        """Test section title detection."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        analyzer = StructureAnalyzer()

        section_slide = SlideNode(slide_number=1, slide_id="slide_1")
        section_slide.title = "Part 1: Introduction"
        section_slide.bullets = []

        assert analyzer._is_section_title(section_slide) is True


        content_slide = SlideNode(slide_number=2, slide_id="slide_2")
        content_slide.bullets = [
            BulletPoint(text="Point 1", level=0, index=0),
            BulletPoint(text="Point 2", level=0, index=1),
            BulletPoint(text="Point 3", level=0, index=2),
        ]

        assert analyzer._is_section_title(content_slide) is False

    def test_extract_topic(self):
        """Test topic extraction."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer

        analyzer = StructureAnalyzer()

        topic = analyzer._extract_topic("Part 1: Machine Learning")
        assert topic == "Machine Learning"

    def test_detect_topics(self):
        """Test topic detection."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Intro",
                bullets=[BulletPoint(text="Welcome", level=0, index=0)],
                topics=["AI", "ML"],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Content",
                bullets=[BulletPoint(text="Point", level=0, index=0)],
                topics=["AI"],
            ),
        ]

        analyzer = StructureAnalyzer()
        topics = analyzer.detect_topics(slides)

        assert isinstance(topics, dict)

    def test_detect_repeated_themes(self):
        """Test repeated theme detection."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Slide 1",
                bullets=[BulletPoint(text="important concept here", level=0, index=0)],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Slide 2",
                bullets=[
                    BulletPoint(text="important concept repeated", level=0, index=0)
                ],
            ),
        ]

        analyzer = StructureAnalyzer()
        themes = analyzer.detect_repeated_themes(slides)

        assert isinstance(themes, dict)

    def test_compute_slide_similarity_with_embeddings(self):
        """Test similarity computation with embeddings."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Slide 1",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Slide 2",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
        ]

        embeddings = {
            "slide_1": [0.1] * 384,
            "slide_2": [0.2] * 384,
        }

        analyzer = StructureAnalyzer()
        similarities = analyzer.compute_slide_similarity(slides, embeddings)

        assert "slide_1" in similarities

    def test_compute_slide_similarity_keywords(self):
        """Test similarity computation with keywords."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Slide 1",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
                keywords=["python", "code"],
                topics=["programming"],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Slide 2",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
                keywords=["python", "data"],
                topics=["programming"],
            ),
        ]

        analyzer = StructureAnalyzer()
        similarities = analyzer.compute_slide_similarity(slides)

        assert "slide_1" in similarities

    def test_identify_transitions(self):
        """Test transition identification."""
        from pptx_indexer.core.structure_analyzer import StructureAnalyzer
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Content",
                bullets=[BulletPoint(text="Point", level=0, index=0)],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Conclusion",
                bullets=[BulletPoint(text="Summary", level=0, index=0)],
            ),
        ]

        analyzer = StructureAnalyzer()
        transitions = analyzer.identify_transitions(slides)

        assert isinstance(transitions, list)


class TestSlideGraphBuilderExtended:
    """Extended tests for SlideGraphBuilder."""

    def test_build_graph(self):
        """Test building a complete graph."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint, SectionNode

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Intro",
                bullets=[BulletPoint(text="Welcome", level=0, index=0)],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Content",
                bullets=[BulletPoint(text="Point", level=0, index=0)],
            ),
        ]

        builder = SlideGraphBuilder()

        sections = [
            SectionNode(title="Intro", slide_ids=["slide_1"]),
        ]

        graph = builder.build(slides, sections)

        assert len(graph.nodes) > 0

    def test_add_semantic_edges(self):
        """Test adding semantic edges."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder
        from pptx_indexer.schemas.slide_graph_schema import SlideGraph, SlideGraphNode
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint

        builder = SlideGraphBuilder(similarity_threshold=0.3)

        similarities = {
            "slide_1": {"slide_2": 0.8},
            "slide_2": {"slide_1": 0.8},
        }

        graph = SlideGraph()

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Slide 1",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
            SlideNode(
                slide_number=2,
                slide_id="slide_2",
                title="Slide 2",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
            ),
        ]

        for slide in slides:
            node = SlideGraphNode(
                node_id=slide.slide_id,
                node_type="slide",
                content={"title": slide.title},
            )
            graph.add_node(node)

        builder._add_semantic_edges(graph, similarities)

    def test_expand_with_images(self):
        """Test expanding graph with images."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder
        from pptx_indexer.schemas.slide_graph_schema import SlideGraph, SlideGraphNode
        from pptx_indexer.schemas.slide_node import SlideNode, BulletPoint, ImageNode

        slides = [
            SlideNode(
                slide_number=1,
                slide_id="slide_1",
                title="Slide 1",
                bullets=[BulletPoint(text="Content", level=0, index=0)],
                images=[ImageNode(image_id="img1", image_path="/test.png")],
            ),
        ]

        builder = SlideGraphBuilder()

        graph = SlideGraph()

        for slide in slides:
            node = SlideGraphNode(
                node_id=slide.slide_id,
                node_type="slide",
                content={},
            )
            graph.add_node(node)

        result = builder.expand_with_images(graph, slides)

        assert len(result.nodes) >= len(graph.nodes)

    def test_compute_importance_scores(self):
        """Test computing importance scores."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder
        from pptx_indexer.schemas.slide_graph_schema import SlideGraph, SlideGraphNode

        builder = SlideGraphBuilder()

        graph = SlideGraph()
        node1 = SlideGraphNode(
            node_id="slide_1", node_type="slide", content={"title": "Slide 1"}
        )
        node2 = SlideGraphNode(
            node_id="slide_2", node_type="slide", content={"title": "Slide 2"}
        )
        graph.add_node(node1)
        graph.add_node(node2)

        scores = builder.compute_importance_scores(graph)

        assert len(scores) > 0

    def test_detect_concepts(self):
        """Test concept detection."""
        from pptx_indexer.core.slide_graph import SlideGraphBuilder
        from pptx_indexer.schemas.slide_graph_schema import (
            SlideGraph,
            SlideGraphNode,
            GraphEdge,
            EdgeType,
        )

        builder = SlideGraphBuilder()

        graph = SlideGraph()
        node1 = SlideGraphNode(node_id="slide_1", node_type="slide", content={})
        node2 = SlideGraphNode(node_id="slide_2", node_type="slide", content={})
        graph.add_node(node1)
        graph.add_node(node2)

        edge = GraphEdge(
            source_id="slide_1",
            target_id="slide_2",
            edge_type=EdgeType.SEMANTICALLY_SIMILAR,
            weight=0.8,
        )
        graph.add_edge(edge)

        clusters = builder.detect_concepts(graph)

        assert isinstance(clusters, dict)


class TestParserExtended:
    """Extended tests for PPTParser."""

    @patch("pptx_indexer.core.parser.Presentation")
    def test_parse_presentation(self, mock_pres_class, temp_dir):
        """Test parsing a presentation."""
        from pptx_indexer.core.parser import PPTParser

        mock_slide = Mock()
        mock_slide.slide_layout = Mock()
        mock_slide.slide_layout.name = "Title Slide"
        mock_slide.shapes = []
        mock_slide.has_notes_slide = False

        mock_pres = Mock()
        mock_pres.slides = [mock_slide]
        mock_pres_class.return_value = mock_pres

        parser = PPTParser(output_dir=temp_dir)
        slides = parser.parse("/test.pptx")

        assert len(slides) == 1

    @patch("pptx_indexer.core.parser.Presentation")
    def test_parse_slide_with_text(self, mock_pres_class, temp_dir):
        """Test parsing a slide with text."""
        from pptx_indexer.core.parser import PPTParser

        mock_para = Mock()
        mock_para.text = "Test Title"
        mock_para.level = 0

        mock_text_frame = Mock()
        mock_text_frame.text = "Test Title"
        mock_text_frame.paragraphs = [mock_para]

        mock_shape = Mock()
        mock_shape.has_text_frame = True
        mock_shape.name = "Title 1"
        mock_shape.text_frame = mock_text_frame

        mock_slide = Mock()
        mock_slide.slide_layout = Mock()
        mock_slide.slide_layout.name = "Title Slide"
        mock_slide.shapes = [mock_shape]
        mock_slide.has_notes_slide = False

        mock_pres = Mock()
        mock_pres.slides = [mock_slide]
        mock_pres_class.return_value = mock_pres

        parser = PPTParser(output_dir=temp_dir)
        slides = parser.parse("/test.pptx")

        assert slides[0].title == "Test Title"

    @patch("pptx_indexer.core.parser.Presentation")
    def test_parse_slide_with_bullets(self, mock_pres_class, temp_dir):
        """Test parsing bullets."""
        from pptx_indexer.core.parser import PPTParser

        mock_para = Mock()
        mock_para.text = "Bullet point"
        mock_para.level = 0

        mock_text_frame = Mock()
        mock_text_frame.text = "Content"
        mock_text_frame.paragraphs = [mock_para]

        mock_shape = Mock()
        mock_shape.has_text_frame = True
        mock_shape.name = "Content Placeholder"
        mock_shape.text_frame = mock_text_frame

        mock_slide = Mock()
        mock_slide.slide_layout = Mock()
        mock_slide.slide_layout.name = "Content"
        mock_slide.shapes = [mock_shape]
        mock_slide.has_notes_slide = False

        mock_pres = Mock()
        mock_pres.slides = [mock_slide]
        mock_pres_class.return_value = mock_pres

        parser = PPTParser(output_dir=temp_dir)
        slides = parser.parse("/test.pptx")

        assert len(slides[0].bullets) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
