"""
Embedding Service for StudyRAG
Handles text embedding generation using Google Gemini

This module also supports a MOCK mode for development without
calling the real Google API. Enable it by setting:

    USE_MOCK_EMBEDDINGS=true
"""

from __future__ import annotations

import hashlib
import os
import random
from typing import List

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from backend.config import GOOGLE_API_KEY, EMBEDDING_MODEL


class EmbeddingService:
    """
    Service for generating embeddings using Google Gemini API, with optional mock mode.
    """

    def __init__(self) -> None:
        """Initialize the Google Gemini API with API key or mock mode."""
        self.use_mock = os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"
        self.mock_dim = int(os.getenv("MOCK_EMBEDDING_DIM", "256"))

        if self.use_mock:
            self.model_name = "mock"
            print(
                f"✓ Embedding Service initialized in MOCK mode "
                f"(dimension={self.mock_dim}, no Google API calls)"
            )
        else:
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model_name = EMBEDDING_MODEL
            print(f"✓ Embedding Service initialized with model: {self.model_name}")

    def _mock_embedding(self, text: str) -> List[float]:
        """
        Deterministic mock embedding for a given text.

        Uses a hash of the text as RNG seed so the same text
        always produces the same vector.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], "big")
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(self.mock_dim)]

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        In MOCK mode or on Google API quota errors, this falls back
        to deterministic random vectors so that the rest of the
        pipeline keeps working for development.
        """
        if self.use_mock:
            return self._mock_embedding(text)

        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except google_exceptions.GoogleAPIError as exc:
            # Typical case: 429 quota exceeded
            print(
                f"⚠️ Gemini embed_content error ({type(exc).__name__}): {exc}. "
                "Falling back to MOCK embeddings."
            )
            return self._mock_embedding(text)
        except Exception as exc:  # pragma: no cover - defensive
            print(
                f"⚠️ Unexpected embedding error ({type(exc).__name__}): {exc}. "
                "Falling back to MOCK embeddings."
            )
            return self._mock_embedding(text)

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        """
        if self.use_mock:
            return self._mock_embedding(query)

        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except google_exceptions.GoogleAPIError as exc:
            print(
                f"⚠️ Gemini embed_content (query) error ({type(exc).__name__}): {exc}. "
                "Falling back to MOCK embeddings."
            )
            return self._mock_embedding(query)
        except Exception as exc:  # pragma: no cover - defensive
            print(
                f"⚠️ Unexpected query embedding error ({type(exc).__name__}): {exc}. "
                "Falling back to MOCK embeddings."
            )
            return self._mock_embedding(query)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        """
        return [self.embed_text(text) for text in texts]


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create singleton embedding service instance.

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
