"""
RAG Pipeline for StudyRAG
Handles PDF loading, chunking, and vector store creation
"""
import os
from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP, VECTORSTORE_DIR
from backend.embedding_service import get_embedding_service


class GeminiEmbeddings(Embeddings):
    """
    Wrapper class to make Google Gemini embeddings compatible with LangChain
    """
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search documents"""
        return self.embedding_service.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query text"""
        return self.embedding_service.embed_query(text)


class RAGPipeline:
    """
    RAG Pipeline for processing PDFs and creating vector stores
    """
    
    def __init__(self):
        """Initialize the RAG pipeline"""
        self.embeddings = GeminiEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vectorstore: Optional[FAISS] = None
        print(f"✓ RAG Pipeline initialized (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    
    def load_pdf(self, pdf_path: str) -> List:
        """
        Load and extract text from PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of Document objects
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"📄 Loading PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"✓ Loaded {len(documents)} pages from PDF")
        return documents
    
    def chunk_documents(self, documents: List) -> List:
        """
        Split documents into chunks
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunked Document objects
        """
        print(f"✂️  Splitting documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"✓ Created {len(chunks)} chunks")
        return chunks
    
    def create_vectorstore(self, chunks: List, vectorstore_name: str = "default") -> FAISS:
        """
        Create FAISS vector store from document chunks
        
        Args:
            chunks: List of document chunks
            vectorstore_name: Name for saving the vectorstore
            
        Returns:
            FAISS vectorstore instance
        """
        print(f"🔢 Creating embeddings and vector store...")
        
        # Create vector store
        vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )
        
        # Save to disk
        vectorstore_path = Path(VECTORSTORE_DIR) / vectorstore_name
        vectorstore.save_local(str(vectorstore_path))
        print(f"✓ Vector store saved to: {vectorstore_path}")
        
        self.vectorstore = vectorstore
        return vectorstore
    
    def load_vectorstore(self, vectorstore_name: str = "default") -> FAISS:
        """
        Load existing vector store from disk
        
        Args:
            vectorstore_name: Name of the saved vectorstore
            
        Returns:
            FAISS vectorstore instance
        """
        vectorstore_path = Path(VECTORSTORE_DIR) / vectorstore_name
        
        if not vectorstore_path.exists():
            raise FileNotFoundError(f"Vector store not found: {vectorstore_path}")
        
        print(f"📂 Loading vector store from: {vectorstore_path}")
        vectorstore = FAISS.load_local(
            str(vectorstore_path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        self.vectorstore = vectorstore
        print(f"✓ Vector store loaded successfully")
        return vectorstore
    
    def process_pdf(self, pdf_path: str, vectorstore_name: str = "default") -> FAISS:
        """
        Complete pipeline: Load PDF -> Chunk -> Create Vector Store
        
        Args:
            pdf_path: Path to PDF file
            vectorstore_name: Name for the vectorstore
            
        Returns:
            FAISS vectorstore instance
        """
        print(f"\n{'='*60}")
        print(f"🚀 Starting RAG Pipeline for: {Path(pdf_path).name}")
        print(f"{'='*60}\n")
        
        # Step 1: Load PDF
        documents = self.load_pdf(pdf_path)
        
        # Step 2: Chunk documents
        chunks = self.chunk_documents(documents)
        
        # Step 3: Create vector store
        vectorstore = self.create_vectorstore(chunks, vectorstore_name)
        
        print(f"\n{'='*60}")
        print(f"✅ RAG Pipeline completed successfully!")
        print(f"{'='*60}\n")
        
        return vectorstore


# Singleton instance
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """
    Get or create singleton RAG pipeline instance
    
    Returns:
        RAGPipeline instance
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
