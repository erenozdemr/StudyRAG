"""
Configuration management for StudyRAG
Loads environment variables and provides settings for the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Google Gemini API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please check your .env file.")

# Directory Settings
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "data/uploads")
VECTORSTORE_DIR = BASE_DIR / os.getenv("VECTORSTORE_DIR", "data/vectorstore")

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

# Model Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/embedding-001")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-pro")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))

# Retrieval Settings
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 4))

# Application Info
APP_NAME = "StudyRAG"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "RAG-based Study Assistant with Google Gemini"
