"""
Slide graph schema for hierarchical and semantic relationships.
"""

from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class EdgeType(str, Enum):
    """Types of edges in the slide graph."""
    NEXT = "next"  # Sequential ordering
    PREVIOUS = "previous"  # Reverse sequential
    BELONGS_TO = "belongs_to"  # Slide belongs to section
    SEMANTICALLY_SIMILAR = "semantically_similar"
    REFERENCES = "references"  # Cites or refers to
    CONTAINS = "contains"  # Parent contains child
    EXPANDS = "expands"  # Detailed version of
    SUMMARIZES = "summarizes"  # Summary of
    CONTRASTS = "contrasts"  # Opposes or contrasts with
    RELATED = "related"  # General relationship


@dataclass
class GraphEdge:
    """Represents an edge in the slide graph."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0  # Strength of relationship
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
        }


@dataclass
class SlideGraphNode:
    """Enhanced node representation for graph operations."""
    node_id: str
    node_type: str  # 'slide', 'section', 'concept'
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None
    neighbors: Dict[EdgeType, List[str]] = field(default_factory=dict)

    def get_all_neighbors(self) -> Set[str]:
        """Get all connected nodes."""
        neighbors = set()
        for edge_list in self.neighbors.values():
            neighbors.update(edge_list)
        return neighbors


@dataclass
class SlideGraph:
    """
    Graph representation of entire presentation.
    Supports multi-hop traversal and semantic queries.
    """
    
    # Nodes
    nodes: Dict[str, SlideGraphNode] = field(default_factory=dict)
    
    # Edges
    edges: List[GraphEdge] = field(default_factory=list)
    
    # Metadata
    document_title: str = ""
    document_description: Optional[str] = None
    total_slides: int = 0
    
    # Statistics
    connectivity_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def add_node(self, node: SlideGraphNode) -> None:
        """Add a node to graph."""
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to graph."""
        self.edges.append(edge)
        
        # Update neighbor tracking
        if edge.source_id in self.nodes:
            if edge.edge_type not in self.nodes[edge.source_id].neighbors:
                self.nodes[edge.source_id].neighbors[edge.edge_type] = []
            if edge.target_id not in self.nodes[edge.source_id].neighbors[edge.edge_type]:
                self.nodes[edge.source_id].neighbors[edge.edge_type].append(edge.target_id)

    def get_node(self, node_id: str) -> Optional[SlideGraphNode]:
        """Retrieve a node."""
        return self.nodes.get(node_id)

    def get_neighbors(
        self,
        node_id: str,
        edge_types: Optional[List[EdgeType]] = None,
        max_depth: int = 1,
    ) -> Dict[str, SlideGraphNode]:
        """Get neighboring nodes up to specified depth."""
        if node_id not in self.nodes:
            return {}

        neighbors = {}
        visited = set()
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)
            
            if depth >= max_depth or current_id in visited:
                continue
                
            visited.add(current_id)
            current_node = self.nodes.get(current_id)
            
            if not current_node:
                continue

            for etype, neighbor_list in current_node.neighbors.items():
                if edge_types is None or etype in edge_types:
                    for neighbor_id in neighbor_list:
                        if neighbor_id not in visited:
                            neighbors[neighbor_id] = self.nodes[neighbor_id]
                            if depth + 1 < max_depth:
                                queue.append((neighbor_id, depth + 1))

        return neighbors

    def get_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find shortest path between two nodes (BFS)."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        visited = set()
        queue = [(source_id, [source_id])]

        while queue:
            current_id, path = queue.pop(0)
            
            if current_id == target_id:
                return path
            
            if current_id in visited:
                continue
                
            visited.add(current_id)
            current_node = self.nodes.get(current_id)
            
            if current_node:
                for neighbor_list in current_node.neighbors.values():
                    for neighbor_id in neighbor_list:
                        if neighbor_id not in visited:
                            queue.append((neighbor_id, path + [neighbor_id]))

        return None

    def get_related_slides(
        self,
        slide_id: str,
        relation_types: Optional[List[EdgeType]] = None,
    ) -> List[str]:
        """Get slides related to a given slide."""
        related = []
        
        for edge in self.edges:
            if edge.source_id == slide_id:
                if relation_types is None or edge.edge_type in relation_types:
                    related.append(edge.target_id)

        return related

    def to_dict(self) -> Dict[str, Any]:
        """Export graph to dictionary format."""
        return {
            "document_title": self.document_title,
            "total_slides": self.total_slides,
            "nodes": {
                node_id: node.to_dict() for node_id, node in self.nodes.items()
            },
            "edges": [edge.to_dict() for edge in self.edges],
        }
