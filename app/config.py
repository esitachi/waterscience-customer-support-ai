from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
RESEARCH_DIR = BASE_DIR / "research"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    
    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "groq", "anthropic"
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0

    # Paths
    KNOWLEDGE_BASE_PATH: Path = RESEARCH_DIR / "product_knowledge_base.json"
    SYNTHETIC_CASES_PATH: Path = RESEARCH_DIR / "synthetic_support_cases.json"
    RESEARCH_REGISTER_PATH: Path = RESEARCH_DIR / "research_register.csv"

settings = Settings()
