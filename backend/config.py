"""
RAG 시스템 설정
- 하이브리드 LLM 지원 (OpenAI / Ollama)
- 환경 변수로 설정 가능
"""
from pydantic_settings import BaseSettings
from typing import Literal
import os


class Settings(BaseSettings):
    # LLM 설정
    LLM_PROVIDER: Literal["openai", "ollama"] = "ollama"  # 기본값: Ollama (무료)
    
    # OpenAI 설정
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Ollama 설정
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # 또는 "mistral", "gemma2" 등
    
    # ChromaDB 설정
    CHROMA_PERSIST_PATH: str = "./data/chroma_db"
    COLLECTION_NAME: str = "rag_documents"
    
    # 문서 처리 설정
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # 검색 설정
    TOP_K_RESULTS: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
