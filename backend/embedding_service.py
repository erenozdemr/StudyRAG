"""
Embedding Service for StudyRAG
Handles text embedding generation using Google Gemini
"""
import google.generativeai as genai
from typing import List
from backend.config import GOOGLE_API_KEY, EMBEDDING_MODEL


class EmbeddingService:
    """
    Service for generating embeddings using Google Gemini API
    """
    
    def __init__(self):
        """Initialize the Google Gemini API with API key"""
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model_name = EMBEDDING_MODEL
        print(f"✓ Embedding Service initialized with model: {self.model_name}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        
        Args:
            query: Search query text
            
        Returns:
            List of floats representing the embedding vector
        """
        result = genai.embed_content(
            model=self.model_name,
            content=query,
            task_type="retrieval_query"
        )
        return result['embedding']
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents
        
        Args:
            texts: List of text documents
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.embed_text(text)
            embeddings.append(embedding)
        return embeddings


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create singleton embedding service instance
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
