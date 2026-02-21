"""Default plugins for PPTX Indexer.
Ready-to-use implementations with popular libraries.
"""

# ============= OpenAI LLM Plugin =============

import logging
from typing import List

logger = logging.getLogger(__name__)


class OpenAILLM:
    """OpenAI GPT LLM implementation."""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs

        try:
            import openai

            openai.api_key = api_key
            self.client = openai
        except ImportError:
            raise ImportError("openai package required: pip install openai")

        logger.info(f"Initialized OpenAI LLM: {model}")

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        try:
            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 512),
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text for multiple prompts."""
        return [self.generate(prompt, **kwargs) for prompt in prompts]


# ============= Google Gemini LLM Plugin =============


class GeminiLLM:
    """Google Gemini LLM implementation."""

    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self.client = genai
            self.generation_config = {
                "temperature": kwargs.get("temperature", 0.3),
                "max_output_tokens": kwargs.get("max_tokens", 512),
                "top_p": kwargs.get("top_p", 0.95),
                "top_k": kwargs.get("top_k", 40),
            }
        except ImportError:
            raise ImportError(
                "google-generativeai package required: pip install google-generativeai"
            )

        logger.info(f"Initialized Gemini LLM: {model}")

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        try:
            generation_config = {
                "temperature": kwargs.get("temperature", 0.3),
                "max_output_tokens": kwargs.get("max_tokens", 512),
                "top_p": kwargs.get("top_p", 0.95),
                "top_k": kwargs.get("top_k", 40),
            }

            model = self.client.GenerativeModel(self.model)
            response = model.generate_content(prompt, generation_config=generation_config)

            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text for multiple prompts."""
        return [self.generate(prompt, **kwargs) for prompt in prompts]


# ============= Sentence Transformer Embedder =============


class SentenceTransformerEmbedder:
    """Sentence Transformers embedding implementation."""

    def __init__(self, model: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model
        self.device = device

        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model, device=device)
        except ImportError:
            raise ImportError("sentence-transformers required: pip install sentence-transformers")

        logger.info(f"Initialized SentenceTransformer: {model}")

    def embed(self, text: str) -> List[float]:
        """Embed single text."""
        embedding = self.model.encode(text)
        return embedding.tolist()

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()


# ============= Chroma Vector Store =============


class ChromaVectorStore:
    """Chroma vector database implementation."""

    def __init__(self, collection_name: str = "pptx_index", persist_dir: str = "./chroma_db"):
        try:
            import chromadb

            self.client = chromadb.Client()
            self.collection = self.client.create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            raise ImportError("chromadb required: pip install chromadb")

        logger.info(f"Initialized Chroma collection: {collection_name}")

    def add(self, ids: List[str], vectors: List[List[float]], metadatas: List[dict]) -> None:
        """Add vectors to collection."""
        self.collection.add(
            ids=ids,
            embeddings=vectors,
            metadatas=metadatas,
        )
        logger.debug(f"Added {len(ids)} vectors to Chroma")

    def search(self, query_vector: List[float], top_k: int = 10, threshold: float = None):
        """Search similar vectors."""
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )

        # Transform results format
        output = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                similarity = 1 - distance  # Convert distance to similarity
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                output.append((doc_id, similarity, metadata))

        return output

    def batch_search(self, query_vectors: List[List[float]], top_k: int = 10):
        """Batch search."""
        return [self.search(qv, top_k) for qv in query_vectors]

    def delete(self, ids: List[str]) -> None:
        """Delete vectors."""
        self.collection.delete(ids=ids)

    def clear(self) -> None:
        """Clear collection."""
        self.client.delete_collection(name=self.collection.name)


# ============= Pytesseract OCR =============


class PytesseractOCR:
    """Pytesseract OCR implementation."""

    def __init__(self, lang: str = "eng"):
        try:
            import pytesseract
            from PIL import Image

            self.pytesseract = pytesseract
            self.Image = Image
        except ImportError:
            raise ImportError("pytesseract and Pillow required: pip install pytesseract pillow")

        logger.info(f"Initialized Pytesseract OCR: {lang}")

    def extract_text(self, image_path: str) -> str:
        """Extract text from image."""
        try:
            image = self.Image.open(image_path)
            text = self.pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return ""

    def extract_text_with_coords(self, image_path: str) -> dict:
        """Extract text with coordinates."""
        try:
            image = self.Image.open(image_path)
            data = self.pytesseract.image_to_data(image, output_type="dict")

            blocks = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():
                    blocks.append(
                        {
                            "text": data["text"][i],
                            "bbox": [
                                data["left"][i],
                                data["top"][i],
                                data["left"][i] + data["width"][i],
                                data["top"][i] + data["height"][i],
                            ],
                        }
                    )

            return {
                "text": "\n".join(data["text"]),
                "blocks": blocks,
            }
        except Exception as e:
            logger.error(f"OCR with coords failed: {e}")
            return {"text": "", "blocks": []}


__all__ = [
    "OpenAILLM",
    "GeminiLLM",
    "SentenceTransformerEmbedder",
    "ChromaVectorStore",
    "PytesseractOCR",
]
