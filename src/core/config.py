from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    # Project Info
    PROJECT_NAME: str = "Phone Fraud Detection System"
    PROJECT_VERSION: str = "1.0.0"
    
    # API Keys
    OPIK_API_KEY: str = os.getenv("OPIK_API_KEY", "")
    OPIK_WORKSPACE: str = os.getenv("OPIK_WORKSPACE", "suyodhanj6")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    
    # Model Settings
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    
    # Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "fraud_detection")
    
    # Project Settings
    OPIK_PROJECT_NAME: str = os.getenv("OPIK_PROJECT_NAME", "")
    COMET_URL: str = os.getenv("COMET_URL", "")
    
    # Additional Settings
    USE_LOCAL: bool = os.getenv("USE_LOCAL", "false").lower() == "true"
    FORCE: bool = os.getenv("FORCE", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()

# Create a global settings instance
settings = get_settings() 