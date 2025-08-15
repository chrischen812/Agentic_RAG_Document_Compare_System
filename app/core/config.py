"""
Configuration settings for the Agentic RAG System.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    load_dotenv()  # Loads the .env file contents into environment variables
    
    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # ChromaDB Settings
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "documents")
    
    # Embedding Settings
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # Gemini Settings
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_temperature: float = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    gemini_max_tokens: int = int(os.getenv("GEMINI_MAX_TOKENS", "8192"))
    
    # Chunking Settings
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # PDF Processing Settings
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "50000000"))  # 50MB
    
    # Agent Settings
    max_reasoning_steps: int = int(os.getenv("MAX_REASONING_STEPS", "10"))
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "10"))
    
    # Ontology Settings
    ontology_base_path: str = os.getenv("ONTOLOGY_BASE_PATH", "./ontologies")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Validation
if not settings.gemini_api_key:
    print("WARNING: GEMINI_API_KEY not set. Some features may not work.")

# Create necessary directories
os.makedirs(os.path.dirname(settings.chroma_db_path), exist_ok=True)
os.makedirs(settings.ontology_base_path, exist_ok=True)
