"""
Slide Graph Builder - Creates hierarchical graph structure for semantic traversal.
Enables reasoning-aware retrieval over presentations.
"""

from typing import List, Dict, Optional, Set
import logging

from ..schemas.slide_node import SlideNode, SectionNode
from ..schemas.slide_graph_schema import (
    SlideGraph,
    SlideGraphNode,
    GraphEdge,
    EdgeType,
)

logger = logging.getLogger(__name__)


class SlideGraphBuilder:
    """
    Builds graph representation of presentation with:
    - Sequential edges (NEXT, PREVIOUS)
    - Hierarchical edges (BELONGS_TO, CONTAINS)
    - Semantic edges (SIMILAR, REFERENCES, RELATED)
    """
    
    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold
    
    def build(
        self,
        slides: List[SlideNode],
        sections: List[SectionNode],
        similarities: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> SlideGraph:
        """
        Build complete graph from slides and sections.
        
        Args:
            slides: List of slide nodes
            sections: List of section nodes
            similarities: Pre-computed similarity matrix
        
        Returns:
            Complete SlideGraph
        """
        logger.info(f"Building graph with {len(slides)} slides and {len(sections)} sections")
        
        graph = SlideGraph()
        
        # Add all slides as nodes
        for slide in slides:
            node = self._create_slide_node(slide)
            graph.add_node(node)
        
        # Add all sections as nodes
        for section in sections:
            node = self._create_section_node(section)
            graph.add_node(node)
        
        # Add sequential edges (NEXT, PREVIOUS)
        self._add_sequential_edges(graph, slides)
        
        # Add hierarchical edges (BELONGS_TO, CONTAINS)
        self._add_hierarchical_edges(graph, slides, sections)
        
        # Add semantic edges
        if similarities:
            self._add_semantic_edges(graph, similarities)
        
        # Add reference edges
        self._add_reference_edges(graph, slides)
        
        graph.document_title = "Presentation Graph"
        graph.total_slides = len(slides)
        
        logger.info(f"Graph built with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        return graph
    
    def _create_slide_node(self, slide: SlideNode) -> SlideGraphNode:
        """Convert slide to graph node."""
        content = {
            "title": slide.title,
            "summary": slide.summary or slide.get_full_text()[:200],
            "keywords": slide.keywords,
            "topics": slide.topics,
        }
        
        return SlideGraphNode(
            node_id=slide.slide_id,
            node_type="slide",
            content=content,
            embedding=slide.embedding,
        )
    
    def _create_section_node(self, section: SectionNode) -> SlideGraphNode:
        """Convert section to graph node."""
        content = {
            "title": section.title,
            "description": section.description,
            "topic": section.topic,
            "subtopics": section.subtopics,
        }
        
        return SlideGraphNode(
            node_id=section.section_id,
            node_type="section",
            content=content,
            embedding=section.embedding,
        )
    
    def _add_sequential_edges(self, graph: SlideGraph, slides: List[SlideNode]) -> None:
        """Add NEXT/PREVIOUS edges for slide sequence."""
        
        for i in range(len(slides) - 1):
            current_slide = slides[i]
            next_slide = slides[i + 1]
            
            # Forward edge
            edge_forward = GraphEdge(
                source_id=current_slide.slide_id,
                target_id=next_slide.slide_id,
                edge_type=EdgeType.NEXT,
                weight=1.0,
            )
            graph.add_edge(edge_forward)
            
            # Backward edge
            edge_backward = GraphEdge(
                source_id=next_slide.slide_id,
                target_id=current_slide.slide_id,
                edge_type=EdgeType.PREVIOUS,
                weight=1.0,
            )
            graph.add_edge(edge_backward)
        
        logger.debug(f"Added {len(slides)-1} sequential edge pairs")
    
    def _add_hierarchical_edges(
        self,
        graph: SlideGraph,
        slides: List[SlideNode],
        sections: List[SectionNode],
    ) -> None:
        """Add BELONGS_TO and CONTAINS edges."""
        
        slide_map = {s.slide_id: s for s in slides}
        
        for section in sections:
            for slide_id in section.slide_ids:
                # BELONGS_TO: slide -> section
                edge = GraphEdge(
                    source_id=slide_id,
                    target_id=section.section_id,
                    edge_type=EdgeType.BELONGS_TO,
                    weight=1.0,
                )
                graph.add_edge(edge)
                
                # CONTAINS: section -> slide
                edge_reverse = GraphEdge(
                    source_id=section.section_id,
                    target_id=slide_id,
                    edge_type=EdgeType.CONTAINS,
                    weight=1.0,
                )
                graph.add_edge(edge_reverse)
        
        logger.debug(f"Added hierarchical edges for {len(sections)} sections")
    
    def _add_semantic_edges(
        self,
        graph: SlideGraph,
        similarities: Dict[str, Dict[str, float]],
    ) -> None:
        """Add SEMANTICALLY_SIMILAR edges based on similarity matrix."""
        
        edges_added = 0
        
        for slide_id1, similarity_dict in similarities.items():
            for slide_id2, similarity_score in similarity_dict.items():
                if similarity_score >= self.similarity_threshold and slide_id1 != slide_id2:
                    # Only add one direction to avoid duplication
                    if slide_id1 < slide_id2:
                        edge = GraphEdge(
                            source_id=slide_id1,
                            target_id=slide_id2,
                            edge_type=EdgeType.SEMANTICALLY_SIMILAR,
                            weight=similarity_score,
                        )
                        graph.add_edge(edge)
                        edges_added += 1
        
        logger.debug(f"Added {edges_added} semantic edges")
    
    def _add_reference_edges(self, graph: SlideGraph, slides: List[SlideNode]) -> None:
        """Add REFERENCES edges from slide.references."""
        
        edges_added = 0
        
        for slide in slides:
            for ref_id in slide.references:
                if ref_id in {s.slide_id for s in slides}:
                    edge = GraphEdge(
                        source_id=slide.slide_id,
                        target_id=ref_id,
                        edge_type=EdgeType.REFERENCES,
                        weight=1.0,
                    )
                    graph.add_edge(edge)
                    edges_added += 1
        
        logger.debug(f"Added {edges_added} reference edges")
    
    def expand_with_images(
        self,
        graph: SlideGraph,
        slides: List[SlideNode],
    ) -> SlideGraph:
        """Expand graph to include image nodes."""
        
        for slide in slides:
            for image in slide.images:
                # Create image node
                image_node = SlideGraphNode(
                    node_id=image.image_id,
                    node_type="image",
                    content={
                        "caption": image.caption or "",
                        "ocr_text": image.ocr_text or "",
                        "keywords": image.keywords,
                    },
                    embedding=image.embedding,
                )
                graph.add_node(image_node)
                
                # Connect to parent slide
                edge = GraphEdge(
                    source_id=slide.slide_id,
                    target_id=image.image_id,
                    edge_type=EdgeType.CONTAINS,
                    weight=1.0,
                )
                graph.add_edge(edge)
        
        logger.debug(f"Added image nodes to graph")
        return graph
    
    def compute_importance_scores(self, graph: SlideGraph) -> Dict[str, float]:
        """
        Compute importance scores for nodes based on graph centrality.
        Uses weighted degree centrality.
        """
        scores = {}
        
        for node_id, node in graph.nodes.items():
            # Calculate weighted degree
            total_weight = 0.0
            
            for neighbor_list in node.neighbors.values():
                for edge in graph.edges:
                    if (edge.source_id == node_id or edge.target_id == node_id):
                        total_weight += edge.weight
            
            # Normalize by number of nodes
            scores[node_id] = min(total_weight / len(graph.nodes), 1.0)
        
        return scores
    
    def detect_concepts(self, graph: SlideGraph, min_cluster_size: int = 2) -> Dict[int, List[str]]:
        """
        Detect concept clusters by analyzing semantic similarity edges.
        """
        # Build adjacency from semantic edges
        semantic_graph = {}
        
        for edge in graph.edges:
            if edge.edge_type == EdgeType.SEMANTICALLY_SIMILAR:
                if edge.source_id not in semantic_graph:
                    semantic_graph[edge.source_id] = []
                semantic_graph[edge.source_id].append(
                    (edge.target_id, edge.weight)
                )
        
        # Simple clustering using connected components
        visited = set()
        clusters = {}
        cluster_id = 0
        
        for node_id in semantic_graph:
            if node_id not in visited:
                cluster = self._dfs_cluster(node_id, semantic_graph, visited)
                
                if len(cluster) >= min_cluster_size:
                    clusters[cluster_id] = cluster
                    cluster_id += 1
        
        logger.debug(f"Detected {len(clusters)} concept clusters")
        return clusters
    
    @staticmethod
    def _dfs_cluster(node_id: str, graph: Dict, visited: Set[str]) -> List[str]:
        """DFS to find connected component."""
        cluster = []
        stack = [node_id]
        
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                cluster.append(current)
                
                if current in graph:
                    for neighbor, _ in graph[current]:
                        if neighbor not in visited:
                            stack.append(neighbor)
        
        return cluster
