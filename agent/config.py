"""Configuration settings"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY: Optional[str] = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Model configuration - using Descartes with Groq provider
    DEFAULT_MODEL: str = os.getenv('OPENROUTER_MODEL', 'openai/gpt-oss-120b:groq')
    
    # Provider configuration
    @classmethod
    def get_provider_order(cls) -> list:
        """Get provider order as a list"""
        provider_str = os.getenv('OPENROUTER_PROVIDER_ORDER', 'groq')
        return [p.strip() for p in provider_str.split(',')]
    
    ALLOW_FALLBACKS: bool = os.getenv('OPENROUTER_ALLOW_FALLBACKS', 'False').lower() == 'true'
    
    # Data path
    DEFAULT_CSV_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'mock.csv'
    )
    
    # Agent settings
    TEMPERATURE: float = float(os.getenv('OPENROUTER_TEMPERATURE', '0.0'))  # Default 0.0 for deterministic responses
    
    # Web search settings (optional, can cause rate limiting)
    USE_WEB_SEARCH: bool = os.getenv('USE_WEB_SEARCH', 'False').lower() == 'true'  # Disable by default
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Please set it in your environment or .env file."
            )
        return True

