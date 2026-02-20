"""
Base plugin interface for PPTX Indexer.
All models follow this abstraction layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


# ============= LLM Plugin =============

class BaseLLM(ABC):
    """Base class for LLM implementations."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc)
        
        Returns:
            Generated text
        """
        raise NotImplementedError
    
    @abstractmethod
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text for multiple prompts."""
        raise NotImplementedError


# ============= Embedder Plugin =============

class BaseEmbedder(ABC):
    """Base class for embedding model implementations."""
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Embed a single text string.
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector
        """
        raise NotImplementedError
    
    @abstractmethod
    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Return embedding dimension."""
        raise NotImplementedError


# ============= Vector Store Plugin =============

class BaseVectorStore(ABC):
    """Base class for vector database implementations."""
    
    @abstractmethod
    def add(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Add vectors to store.
        
        Args:
            ids: Document IDs
            vectors: Embedding vectors
            metadatas: Metadata for each vector
        """
        raise NotImplementedError
    
    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        threshold: Optional[float] = None,
    ) -> List[tuple[str, float, Dict[str, Any]]]:
        """
        Semantic search.
        
        Returns:
            List of (id, similarity_score, metadata) tuples
        """
        raise NotImplementedError
    
    @abstractmethod
    def batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int = 10,
    ) -> List[List[tuple[str, float, Dict[str, Any]]]]:
        """Search with multiple query vectors."""
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        raise NotImplementedError
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all vectors."""
        raise NotImplementedError


# ============= OCR Plugin =============

class BaseOCR(ABC):
    """Base class for OCR implementations."""
    
    @abstractmethod
    def extract_text(self, image_path: str) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Extracted text
        """
        raise NotImplementedError
    
    @abstractmethod
    def extract_text_with_coords(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text and coordinates.
        
        Returns:
            {
                'text': str,
                'blocks': [{'text': str, 'bbox': [x1, y1, x2, y2]}]
            }
        """
        raise NotImplementedError


# ============= Image Captioner Plugin =============

class BaseImageCaptioner(ABC):
    """Base class for image captioning implementations."""
    
    @abstractmethod
    def caption(self, image_path: str) -> str:
        """
        Generate caption for image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Generated caption
        """
        raise NotImplementedError
    
    @abstractmethod
    def batch_caption(self, image_paths: List[str]) -> List[str]:
        """Generate captions for multiple images."""
        raise NotImplementedError


# ============= Graph Database Plugin =============

class BaseGraphDB(ABC):
    """Base class for graph database implementations."""
    
    @abstractmethod
    def add_node(self, node_id: str, node_type: str, properties: Dict[str, Any]) -> None:
        """Add a node to the graph."""
        raise NotImplementedError
    
    @abstractmethod
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an edge to the graph."""
        raise NotImplementedError
    
    @abstractmethod
    def query_neighbors(
        self,
        node_id: str,
        edge_types: Optional[List[str]] = None,
        max_depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """Query neighboring nodes."""
        raise NotImplementedError
    
    @abstractmethod
    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find path between nodes."""
        raise NotImplementedError
    
    @abstractmethod
    def export(self) -> Dict[str, Any]:
        """Export graph structure."""
        raise NotImplementedError


# ============= Plugin Registry =============

@dataclass
class PluginRegistry:
    """Registry for managing plugins."""
    
    llm: Optional[BaseLLM] = None
    embedder: Optional[BaseEmbedder] = None
    vector_store: Optional[BaseVectorStore] = None
    ocr: Optional[BaseOCR] = None
    image_captioner: Optional[BaseImageCaptioner] = None
    graph_db: Optional[BaseGraphDB] = None
    
    def validate(self) -> bool:
        """Check if all required plugins are set."""
        required = [self.llm, self.embedder, self.vector_store]
        return all(p is not None for p in required)
