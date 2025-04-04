import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "BPK Legal Document API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: Optional[str] = os.getenv(
        "OPENAI_BASE_URL", 
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "qwen2.5-72b-instruct")
    
    # Scraper settings
    MAX_PAGES_DEFAULT: int = int(os.getenv("MAX_PAGES_DEFAULT", "5"))
    MAX_RESULTS_DEFAULT: int = int(os.getenv("MAX_RESULTS_DEFAULT", "10"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Feature toggles
    ENABLE_BPK_SCRAPER: bool = os.getenv("ENABLE_BPK_SCRAPER", "True").lower() == "true"
    ENABLE_PERATURAN_SCRAPER: bool = os.getenv("ENABLE_PERATURAN_SCRAPER", "True").lower() == "true"
    ENABLE_OPENAI: bool = os.getenv("ENABLE_OPENAI", "True").lower() == "true"
    ENABLE_INDOBERT: bool = os.getenv("ENABLE_INDOBERT", "True").lower() == "true"
    
    # Cache settings
    CACHE_RESULTS: bool = os.getenv("CACHE_RESULTS", "True").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get the application settings from cache."""
    return Settings()