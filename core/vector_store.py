"""Vector store abstraction with multiple backend implementations.

Provides a unified interface for vector storage with swappable backends:
- Chroma (default, local)
- Qdrant (cloud/self-hosted)
- Pinecone (cloud)

Supports:
- Add, update, delete operations
- Similarity search with filters
- Metadata storage
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with score and metadata."""
    id: str
    score: float
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingCache:
    """File-based embedding cache."""

    def __init__(self, cache_dir: str = "./data/cache/embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, List[float]] = {}

    def _get_cache_key(self, text: str, model: str) -> str:
        key_str = json.dumps({"text": text, "model": model}, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        key = self._get_cache_key(text, model)
        
        # Check memory cache first
        if key in self._memory_cache:
            return self._memory_cache[key]
        
        # Check file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                self._memory_cache[key] = data["embedding"]
                return data["embedding"]
            except (json.JSONDecodeError, KeyError):
                pass
        return None

    def set(self, text: str, model: str, embedding: List[float]):
        key = self._get_cache_key(text, model)
        self._memory_cache[key] = embedding
        
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps({"embedding": embedding}))


class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
    ):
        """Add documents to the store."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """Search for similar documents."""
        pass

    @abstractmethod
    def delete(self, ids: List[str]):
        """Delete documents by ID."""
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[SearchResult]:
        """Get document by ID."""
        pass

    @abstractmethod
    def persist(self):
        """Persist the store to disk."""
        pass


class ChromaVectorStore(BaseVectorStore):
    """Chroma vector store implementation."""

    def __init__(
        self,
        collection_name: str = "slides",
        persist_directory: str = "./data/chroma",
        distance_metric: str = "cosine",
    ):
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError("chromadb required: pip install chromadb")

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        
        self.collection_name = collection_name
        self.distance_metric = distance_metric
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": distance_metric},
        )
        
        logger.info(f"Initialized ChromaVectorStore: {collection_name}")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
    ):
        if not ids:
            return
            
        meta = metadata or [{}] * len(ids)
        
        # Ensure all IDs are strings
        ids = [str(i) for i in ids]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=meta,
        )
        logger.debug(f"Added {len(ids)} documents to {self.collection_name}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[SearchResult]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter,
        )
        
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                search_results.append(SearchResult(
                    id=doc_id,
                    score=1 - results["distances"][0][i],  # Convert distance to similarity
                    text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                ))
        
        return search_results

    def delete(self, ids: List[str]):
        ids = [str(i) for i in ids]
        self.collection.delete(ids=ids)
        logger.debug(f"Deleted {len(ids)} documents from {self.collection_name}")

    def get_by_id(self, id: str) -> Optional[SearchResult]:
        try:
            result = self.collection.get(ids=[str(id)])
            if result["ids"]:
                return SearchResult(
                    id=result["ids"][0],
                    score=1.0,
                    text=result["documents"][0],
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                )
        except Exception as e:
            logger.warning(f"Failed to get document {id}: {e}")
        return None

    def persist(self):
        # Chroma auto-persists with PersistentClient
        pass

    def count(self) -> int:
        return self.collection.count()


class QdrantVectorStore(BaseVectorStore):
    """Qdrant vector store implementation (cloud/self-hosted)."""

    def __init__(
        self,
        collection_name: str = "slides",
        api_key: Optional[str] = None,
        url: str = "localhost",
        port: int = 6333,
    ):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError:
            raise ImportError("qdrant-client required: pip install qdrant-client")

        self.client = QdrantClient(url=url, api_key=api_key, port=port)
        self.collection_name = collection_name
        
        # Create collection if not exists
        try:
            self.client.get_collection(collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        
        logger.info(f"Initialized QdrantVectorStore: {collection_name}")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
    ):
        from qdrant_client.models import PointStruct
        
        if not ids:
            return
            
        points = [
            PointStruct(
                id=str(i),
                vector=emb,
                payload={"text": txt, **(meta or {})},
            )
            for i, emb, txt, meta in zip(ids, embeddings, texts, metadata or [{}] * len(ids))
        ]
        
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[SearchResult]:
        from qdrant_client.models import Filter, FieldCondition, Match
        
        search_filter = None
        if filter:
            search_filter = Filter(
                must=[
                    FieldCondition(key=k, match=Match(value=v))
                    for k, v in filter.items()
                ]
            )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter,
        )
        
        return [
            SearchResult(
                id=str(r.id),
                score=r.score,
                text=r.payload.get("text", ""),
                metadata={k: v for k, v in r.payload.items() if k != "text"},
            )
            for r in results
        ]

    def delete(self, ids: List[str]):
        from qdrant_client.models import Filter, PointIdsList
        
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=ids),
        )

    def get_by_id(self, id: str) -> Optional[SearchResult]:
        results = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[id],
        )
        if results:
            r = results[0]
            return SearchResult(
                id=str(r.id),
                score=1.0,
                text=r.payload.get("text", ""),
                metadata={k: v for k, v in r.payload.items() if k != "text"},
            )
        return None

    def persist(self):
        # Qdrant auto-persists
        pass


class VectorStoreFactory:
    """Factory for creating vector store instances."""

    @staticmethod
    def create(
        provider: Optional[str] = None,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> BaseVectorStore:
        config = get_config()
        
        provider = provider or config.vector_store.provider
        collection_name = collection_name or config.vector_store.collection_name
        
        stores = {
            "chroma": ChromaVectorStore,
            "qdrant": QdrantVectorStore,
        }
        
        store_class = stores.get(provider.lower())
        if not store_class:
            raise ValueError(f"Unknown vector store provider: {provider}")
        
        if provider == "chroma":
            return store_class(
                collection_name=collection_name,
                persist_directory=kwargs.get("persist_directory", config.vector_store.persist_directory),
                distance_metric=kwargs.get("distance_metric", config.vector_store.distance_metric),
            )
        elif provider == "qdrant":
            return store_class(
                collection_name=collection_name,
                api_key=kwargs.get("api_key"),
                url=kwargs.get("url", "localhost"),
                port=kwargs.get("port", 6333),
            )
        
        return store_class(collection_name=collection_name, **kwargs)


def create_vector_store(**kwargs) -> BaseVectorStore:
    """Factory function to create vector store from config."""
    return VectorStoreFactory.create(**kwargs)
