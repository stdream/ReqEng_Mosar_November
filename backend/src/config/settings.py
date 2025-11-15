"""
Configuration settings for MOSAR GraphRAG API
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    APP_NAME: str = "MOSAR GraphRAG API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # Neo4j Settings
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str

    # OpenAI Settings (for GraphRAG)
    OPENAI_API_KEY: Optional[str] = None

    # Anthropic Settings (alternative)
    ANTHROPIC_API_KEY: Optional[str] = None

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",
    ]

    # Vector Search Settings
    VECTOR_TOP_K: int = 10
    SIMILARITY_THRESHOLD: float = 0.75

    class Config:
        env_file = "../.env"
        case_sensitive = True


# Global settings instance
settings = Settings()
