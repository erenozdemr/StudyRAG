"""
Retrieval Service for StudyRAG
Handles similarity search and question answering using Google Gemini
"""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from backend.config import GOOGLE_API_KEY, LLM_MODEL, TEMPERATURE, MAX_TOKENS, TOP_K_RESULTS
from backend.rag_pipeline import get_rag_pipeline


class RetrievalService:
    """
    Service for retrieving relevant documents and generating answers
    """
    
    def __init__(self):
        """Initialize the retrieval service with Google Gemini"""
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)
        self.rag_pipeline = get_rag_pipeline()
        self.generation_config = {
            "temperature": TEMPERATURE,
            "max_output_tokens": MAX_TOKENS,
        }
        print(f"✓ Retrieval Service initialized with model: {LLM_MODEL}")
    
    def retrieve_documents(self, query: str, k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant documents for a query
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of dictionaries containing document content and metadata
        """
        if self.rag_pipeline.vectorstore is None:
            raise ValueError("No vector store loaded. Please process a PDF first.")
        
        # Similarity search
        docs = self.rag_pipeline.vectorstore.similarity_search(query, k=k)
        
        # Format results
        results = []
        for i, doc in enumerate(docs):
            results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", "unknown"),
                "rank": i + 1
            })
        
        return results
    
    def build_context_from_docs(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for doc in documents:
            context_parts.append(
                f"[Kaynak {doc['rank']} - Sayfa {doc['page']}]\n{doc['content']}\n"
            )
        return "\n".join(context_parts)
    
    def create_rag_prompt(self, query: str, context: str) -> str:
        """
        Create RAG prompt in Turkish
        
        Args:
            query: User question
            context: Retrieved context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""Sen bir ders notu asistanısın. Verilen ders notlarına dayanarak soruları cevaplıyorsun.

**BAĞLAM (Ders Notlarından):**
{context}

**SORU:**
{query}

**TALİMATLAR:**
1. Sadece verilen bağlamdaki bilgileri kullan
2. Cevabını Türkçe ver
3. Net ve anlaşılır ol
4. Eğer bağlamda cevap yoksa, "Bu soru ile ilgili ders notlarında bilgi bulamadım" de
5. Hangi kaynaktan bilgi aldığını belirt (örn: "Sayfa 5'e göre...")

**CEVAP:**"""
        return prompt
    
    def ask(
        self,
        question: str,
        k: int = TOP_K_RESULTS,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG
        
        Args:
            question: User's question
            k: Number of documents to retrieve
            include_sources: Whether to include source documents in response
            
        Returns:
            Dictionary with answer and optional sources
        """
        print(f"\n❓ Question: {question}")
        
        # Step 1: Retrieve relevant documents
        print(f"🔍 Retrieving top {k} relevant documents...")
        documents = self.retrieve_documents(question, k=k)
        
        # Step 2: Build context
        context = self.build_context_from_docs(documents)
        
        # Step 3: Create prompt
        prompt = self.create_rag_prompt(question, context)
        
        # Step 4: Generate answer with Gemini
        print(f"🤖 Generating answer with {LLM_MODEL}...")
        response = self.model.generate_content(
            prompt,
            generation_config=self.generation_config
        )
        
        answer = response.text
        print(f"✓ Answer generated")
        
        # Prepare response
        result = {
            "question": question,
            "answer": answer,
            "model": LLM_MODEL
        }
        
        if include_sources:
            result["sources"] = documents
            result["num_sources"] = len(documents)
        
        return result
    
    def load_vectorstore(self, vectorstore_name: str = "default"):
        """
        Load a vector store for retrieval
        
        Args:
            vectorstore_name: Name of the vectorstore to load
        """
        self.rag_pipeline.load_vectorstore(vectorstore_name)


# Singleton instance
_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    """
    Get or create singleton retrieval service instance
    
    Returns:
        RetrievalService instance
    """
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
