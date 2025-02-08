from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    # Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "fraud_detection")
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    OPIK_API_KEY: str = os.getenv("OPIK_API_KEY", "")
    OPIK_PROJECT_NAME: str = os.getenv("OPIK_PROJECT_NAME", "")
    OPIK_WORKSPACE: str = os.getenv("OPIK_WORKSPACE", "suyodhanj6")
    COMET_URL: str = os.getenv("COMET_URL", "")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields

@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get cached database settings"""
    return DatabaseSettings() 