"""Extended tests for pipelines and plugins to improve coverage."""

from unittest.mock import Mock

import pytest


class TestPPTIndexerExtended:
    """Extended tests for PPTIndexer."""

    def test_indexer_initialization(self):
        """Test indexer initialization."""
        from pptx_indexer.pipelines.indexing_pipeline import PPTIndexer

        mock_llm = Mock()
        mock_llm.generate.return_value = '["test"]'

        mock_embedder = Mock()
        mock_embedder.batch_embed.return_value = [[0.1] * 384]
        mock_embedder.embed.return_value = [0.1] * 384

        mock_vector_store = Mock()

        indexer = PPTIndexer(
            llm=mock_llm,
            embedder=mock_embedder,
            vector_store=mock_vector_store,
        )

        assert indexer.plugins.embedder is not None
        assert indexer.plugins.llm is not None

    def test_index_file_validation(self):
        """Test file validation in index_file."""
        from pptx_indexer.pipelines.indexing_pipeline import PPTIndexer

        mock_llm = Mock()
        mock_llm.generate.return_value = '["test"]'

        mock_embedder = Mock()
        mock_embedder.batch_embed.return_value = [[0.1] * 384]
        mock_embedder.embed.return_value = [0.1] * 384

        mock_vector_store = Mock()

        indexer = PPTIndexer(
            llm=mock_llm,
            embedder=mock_embedder,
            vector_store=mock_vector_store,
        )

        with pytest.raises(ValueError):
            indexer.index_file("test.txt")

    def test_index_file_not_found(self):
        """Test file not found handling."""
        from pptx_indexer.pipelines.indexing_pipeline import PPTIndexer

        mock_llm = Mock()
        mock_llm.generate.return_value = '["test"]'

        mock_embedder = Mock()
        mock_embedder.batch_embed.return_value = [[0.1] * 384]
        mock_embedder.embed.return_value = [0.1] * 384

        mock_vector_store = Mock()

        indexer = PPTIndexer(
            llm=mock_llm,
            embedder=mock_embedder,
            vector_store=mock_vector_store,
        )

        with pytest.raises(FileNotFoundError):
            indexer.index_file("nonexistent.pptx")

    def test_update_plugins(self):
        """Test updating plugins."""
        from pptx_indexer.pipelines.indexing_pipeline import PPTIndexer

        mock_llm = Mock()
        mock_llm.generate.return_value = '["test"]'

        mock_embedder = Mock()
        mock_embedder.batch_embed.return_value = [[0.1] * 384]
        mock_embedder.embed.return_value = [0.1] * 384

        mock_vector_store = Mock()

        indexer = PPTIndexer(
            llm=mock_llm,
            embedder=mock_embedder,
            vector_store=mock_vector_store,
        )

        new_llm = Mock()
        indexer.update_plugins(llm=new_llm)

        assert indexer.plugins.llm is new_llm


class TestPPTRetrieverExtended:
    """Extended tests for PPTRetriever."""

    def test_retriever_initialization(self):
        """Test retriever initialization."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )

        mock_embedder = Mock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
        )

        assert retriever.index is not None
        assert retriever.embedder is not None

    def test_semantic_search_with_vector_store(self):
        """Test semantic search with vector store."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex
        from pptx_indexer.schemas.slide_node import SlideNode

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        index.add_slide(
            SlideNode(slide_id="slide_1", slide_number=1, title="Test Slide")
        )

        mock_embedder = Mock()
        mock_embedder.embed.return_value = [0.1] * 384

        mock_store = Mock()
        mock_store.search.return_value = [("slide_1", 0.9, {"type": "slide"})]

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
            vector_store=mock_store,
        )

        results = retriever._semantic_search("test query", 5)

        assert len(results) > 0

    def test_semantic_search_without_vector_store(self):
        """Test semantic search without vector store."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex
        from pptx_indexer.schemas.slide_node import SlideNode

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        slide = SlideNode(slide_id="slide_1", slide_number=1, title="Test Slide")
        slide.embedding = [0.1] * 384
        index.add_slide(slide)
        index.slide_embeddings = {"slide_1": [0.1] * 384}

        mock_embedder = Mock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
        )

        results = retriever._semantic_search("test query", 5)

        assert len(results) > 0

    def test_keyword_search(self):
        """Test keyword search."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex
        from pptx_indexer.schemas.slide_node import SlideNode

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        index.add_slide(
            SlideNode(slide_id="slide_1", slide_number=1, title="Python Tutorial")
        )

        mock_embedder = Mock()

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
        )

        results = retriever._keyword_search("python", 5)

        assert len(results) > 0

    def test_keyword_search_no_matches(self):
        """Test keyword search with no matches."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex
        from pptx_indexer.schemas.slide_node import SlideNode

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        index.add_slide(
            SlideNode(slide_id="slide_1", slide_number=1, title="Other Content")
        )

        mock_embedder = Mock()

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
        )

        results = retriever._keyword_search("python", 5)

        assert len(results) == 0

    def test_graph_search(self):
        """Test graph search."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex
        from pptx_indexer.schemas.slide_node import SlideNode

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        slide = SlideNode(slide_id="slide_1", slide_number=1, title="Test Slide")
        slide.embedding = [0.1] * 384
        index.add_slide(slide)
        index.slide_embeddings = {"slide_1": [0.1] * 384}

        mock_embedder = Mock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
        )

        results = retriever._graph_search("test", 5)

        assert isinstance(results, list)

    def test_hybrid_search(self):
        """Test hybrid search."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex
        from pptx_indexer.schemas.slide_node import SlideNode

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        slide = SlideNode(slide_id="slide_1", slide_number=1, title="Python Tutorial")
        slide.embedding = [0.1] * 384
        index.add_slide(slide)
        index.slide_embeddings = {"slide_1": [0.1] * 384}

        mock_embedder = Mock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
        )

        results = retriever._hybrid_search("python tutorial", 5)

        assert len(results) > 0
        assert results[0].retrieval_method == "hybrid"

    def test_search_invalid_method(self):
        """Test search with invalid method."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )

        mock_embedder = Mock()

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
        )

        with pytest.raises(ValueError):
            retriever.search("test", method="invalid")

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        sim = PPTRetriever._cosine_similarity(vec1, vec2)

        assert sim == 1.0

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever

        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        sim = PPTRetriever._cosine_similarity(vec1, vec2)

        assert sim == 0.0

    def test_get_context(self):
        """Test get context."""
        from pptx_indexer.pipelines.retrieval_pipeline import PPTRetriever
        from pptx_indexer.schemas.document_index import DocumentIndex
        from pptx_indexer.schemas.slide_node import SlideNode

        index = DocumentIndex(
            document_id="doc1",
            document_title="Test",
            document_path="/test.pptx",
        )
        index.add_slide(
            SlideNode(slide_id="slide_1", slide_number=1, title="Test Slide")
        )

        mock_embedder = Mock()

        retriever = PPTRetriever(
            index=index,
            embedder=mock_embedder,
        )

        context = retriever.get_context("slide_1")

        assert "target_slide" in context


class TestRetrievalResult:
    """Tests for RetrievalResult."""

    def test_retrieval_result_creation(self):
        """Test creating a RetrievalResult."""
        from pptx_indexer.pipelines.retrieval_pipeline import RetrievalResult

        result = RetrievalResult(
            slide_id="slide_1",
            slide_title="Test",
            slide_content="Content",
            score=0.9,
            retrieval_method="semantic",
            metadata={"key": "value"},
        )

        assert result.slide_id == "slide_1"
        assert result.score == 0.9

    def test_retrieval_result_to_dict(self):
        """Test converting RetrievalResult to dict."""
        from pptx_indexer.pipelines.retrieval_pipeline import RetrievalResult

        result = RetrievalResult(
            slide_id="slide_1",
            slide_title="Test",
            slide_content="Content",
            score=0.9,
            retrieval_method="semantic",
            metadata={},
        )

        result_dict = result.to_dict()

        assert result_dict["slide_id"] == "slide_1"
        assert result_dict["score"] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
