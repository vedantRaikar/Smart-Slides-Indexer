"""
Retrieval pipeline for querying indexed presentations.
Supports semantic search, graph traversal, hybrid retrieval.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from ..schemas.document_index import DocumentIndex
from ..schemas.slide_graph_schema import EdgeType
from ..plugins.base_llm import BaseEmbedder, BaseVectorStore

logger = logging.getLogger(__name__)


class RetrievalResult:
    """Result from a retrieval query."""
    
    def __init__(
        self,
        slide_id: str,
        slide_title: str,
        slide_content: str,
        score: float,
        retrieval_method: str,
        metadata: Dict[str, Any],
    ):
        self.slide_id = slide_id
        self.slide_title = slide_title
        self.slide_content = slide_content
        self.score = score
        self.retrieval_method = retrieval_method
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_id": self.slide_id,
            "title": self.slide_title,
            "content": self.slide_content,
            "score": self.score,
            "method": self.retrieval_method,
            "metadata": self.metadata,
        }


class PPTRetriever:
    """
    Retrieval system for indexed presentations.
    
    Supports multiple retrieval modes:
    - Semantic: Use vector search
    - Keyword: keyword matching
    - Graph: Graph traversal
    - Hybrid: Combine multiple methods
    """
    
    def __init__(
        self,
        index: DocumentIndex,
        embedder: BaseEmbedder,
        vector_store: Optional[BaseVectorStore] = None,
    ):
        self.index = index
        self.embedder = embedder
        self.vector_store = vector_store
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        method: str = "hybrid",
        expand_graph: bool = True,
    ) -> List[RetrievalResult]:
        """
        Search for relevant slides.
        
        Args:
            query: Natural language query
            top_k: Number of results
            method: 'semantic', 'keyword', 'graph', 'hybrid'
            expand_graph: Include graph neighbors
        
        Returns:
            List of RetrievalResult
        """
        logger.info(f"Query: '{query}' [method={method}, top_k={top_k}]")
        
        if method == "semantic":
            results = self._semantic_search(query, top_k)
        elif method == "keyword":
            results = self._keyword_search(query, top_k)
        elif method == "graph":
            results = self._graph_search(query, top_k)
        elif method == "hybrid":
            results = self._hybrid_search(query, top_k)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Expand with graph neighbors
        if expand_graph and self.index.graph:
            results = self._expand_with_graph(results, top_k)
        
        logger.info(f"Retrieved {len(results)} results")
        return results
    
    def _semantic_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        """Search using semantic embeddings."""
        
        # Embed query
        query_embedding = self.embedder.embed(query)
        
        results = []
        
        if self.vector_store:
            # Use vector store for fast similarity search
            matches = self.vector_store.search(query_embedding, top_k=top_k)
            
            for slide_id, score, metadata in matches:
                if slide_id in self.index.slides:
                    slide = self.index.slides[slide_id]
                    result = RetrievalResult(
                        slide_id=slide_id,
                        slide_title=slide.title,
                        slide_content=slide.get_full_text()[:200],
                        score=score,
                        retrieval_method="semantic (vector_store)",
                        metadata=metadata,
                    )
                    results.append(result)
        else:
            # Fallback: manual similarity computation
            similarities = []
            
            for slide_id, embedding in self.index.slide_embeddings.items():
                sim = self._cosine_similarity(query_embedding, embedding)
                similarities.append((slide_id, sim))
            
            # Sort and get top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            for slide_id, score in similarities[:top_k]:
                slide = self.index.slides[slide_id]
                result = RetrievalResult(
                    slide_id=slide_id,
                    slide_title=slide.title,
                    slide_content=slide.get_full_text()[:200],
                    score=score,
                    retrieval_method="semantic (manual)",
                    metadata={},
                )
                results.append(result)
        
        return results
    
    def _keyword_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        """Search using keyword matching."""
        
        keywords = query.lower().split()
        scored_slides = {}
        
        # Score slides by keyword matches
        for slide_id, slide in self.index.slides.items():
            score = 0
            text = slide.get_full_text().lower()
            
            for keyword in keywords:
                # Count occurrences
                score += text.count(keyword)
            
            if score > 0:
                scored_slides[slide_id] = score
        
        # Sort and get top_k
        top_slides = sorted(scored_slides.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for slide_id, score in top_slides:
            slide = self.index.slides[slide_id]
            result = RetrievalResult(
                slide_id=slide_id,
                slide_title=slide.title,
                slide_content=slide.get_full_text()[:200],
                score=score / max(1, len(keywords)),  # Normalize
                retrieval_method="keyword",
                metadata={},
            )
            results.append(result)
        
        return results
    
    def _graph_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        """Search using graph traversal."""
        
        # First, find most related slide semantically
        semantic_results = self._semantic_search(query, 1)
        if not semantic_results:
            return []
        
        # Start from best result and expand graph
        root_slide_id = semantic_results[0].slide_id
        
        # Get graph neighbors
        if not self.index.graph:
            return semantic_results
        
        neighbors = self.index.graph.get_neighbors(
            root_slide_id,
            edge_types=[
                EdgeType.SEMANTICALLY_SIMILAR,
                EdgeType.NEXT,
                EdgeType.RELATED,
            ],
            max_depth=2,
        )
        
        # Collect and score results
        results = [semantic_results[0]]
        
        for neighbor_id, neighbor_node in neighbors.items():
            if neighbor_id in self.index.slides:
                slide = self.index.slides[neighbor_id]
                result = RetrievalResult(
                    slide_id=neighbor_id,
                    slide_title=slide.title,
                    slide_content=slide.get_full_text()[:200],
                    score=0.5,  # Lower score for indirect results
                    retrieval_method="graph_expansion",
                    metadata={},
                )
                results.append(result)
        
        return results[:top_k]
    
    def _hybrid_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        """Hybrid search combining multiple methods."""
        
        # Run different search methods
        semantic = self._semantic_search(query, top_k)
        keyword = self._keyword_search(query, top_k)
        
        # Combine and deduplicate
        combined = {}
        
        for result in semantic:
            combined[result.slide_id] = (result, 0.6)  # 60% weight for semantic
        
        for result in keyword:
            if result.slide_id in combined:
                existing, _ = combined[result.slide_id]
                combined[result.slide_id] = (existing, 0.6 + 0.4)
            else:
                combined[result.slide_id] = (result, 0.4)  # 40% weight for keyword
        
        # Sort by combined score
        sorted_results = sorted(combined.values(), key=lambda x: x[1], reverse=True)
        
        results = [result for result, _ in sorted_results[:top_k]]
        
        for result in results:
            result.retrieval_method = "hybrid"
        
        return results
    
    def _expand_with_graph(
        self,
        initial_results: List[RetrievalResult],
        top_k: int,
    ) -> List[RetrievalResult]:
        """Expand results with graph neighbors."""
        
        if not self.index.graph:
            return initial_results
        
        expanded = set()
        
        for result in initial_results:
            expanded.add(result.slide_id)
            
            # Add neighbors
            neighbors = self.index.graph.get_neighbors(
                result.slide_id,
                edge_types=[EdgeType.SEMANTICALLY_SIMILAR, EdgeType.RELATED],
                max_depth=1,
            )
            
            for neighbor_id in neighbors:
                if len(expanded) >= top_k:
                    break
                if neighbor_id not in expanded and neighbor_id in self.index.slides:
                    expanded.add(neighbor_id)
                    slide = self.index.slides[neighbor_id]
                    new_result = RetrievalResult(
                        slide_id=neighbor_id,
                        slide_title=slide.title,
                        slide_content=slide.get_full_text()[:200],
                        score=result.score * 0.8,  # Slightly lower score
                        retrieval_method=result.retrieval_method + "+ graph",
                        metadata={},
                    )
                    initial_results.append(new_result)
        
        return initial_results[:top_k]
    
    @staticmethod
    def _cosine_similarity(
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def get_context(
        self,
        slide_id: str,
        context_radius: int = 2,
    ) -> Dict[str, Any]:
        """
        Get rich context around a slide.
        Includes previous/next slides and related content.
        """
        if slide_id not in self.index.slides:
            return {}
        
        slide = self.index.slides[slide_id]
        context = {
            "target_slide": slide.to_dict(),
            "related_slides": [],
            "section": None,
        }
        
        # Get section
        if slide.section_id in self.index.sections:
            context["section"] = self.index.sections[slide.section_id].to_dict()
        
        # Get related slides from graph
        if self.index.graph:
            related = self.index.graph.get_related_slides(
                slide_id,
                [
                    EdgeType.NEXT,
                    EdgeType.PREVIOUS,
                    EdgeType.SEMANTICALLY_SIMILAR,
                ],
            )
            
            for rel_id in related[:context_radius]:
                if rel_id in self.index.slides:
                    context["related_slides"].append(
                        self.index.slides[rel_id].to_dict()
                    )
        
        return context
