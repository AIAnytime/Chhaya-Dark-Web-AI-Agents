from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Chhaya OS"
    VERSION: str = "1.0.0"
    
    # Tor Configuration
    TOR_PROXY_HOST: str = "127.0.0.1"
    TOR_PROXY_PORT: int = 9050
    TOR_SOCKS_PROXY: str = f"socks5h://{TOR_PROXY_HOST}:{TOR_PROXY_PORT}"
    
    # AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Crawler settings
    DEFAULT_CRAWL_LIMIT: int = 10
    CRAWL_DELAY: float = 2.0
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    ONIONSEARCH_PER_ENGINE_LIMIT: int = 5
    ONIONSEARCH_ENGINES: str = "ahmia,torgle,onionland,phobos,haystack,tor66"
    MAX_TEXT_LENGTH: int = 2000
    MAX_IMAGES: int = 10
    
    # Storage Settings
    OUTPUT_DIR: str = "data"
    PAGES_DIR: str = f"{OUTPUT_DIR}/pages"
    SUMMARY_DIR: str = f"{OUTPUT_DIR}/summary"
    REPORTS_DIR: str = f"{OUTPUT_DIR}/reports"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "chhaya-os-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        case_sensitive = True

settings = Settings()
