from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# .env next to backend/ folder (parent of app/)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH, override=False)


class Settings(BaseSettings):
    openrouter_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    database_url: str = "sqlite+aiosqlite:///./chat.db"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = Field(default="openai/gpt-4o-mini", validation_alias="OPENROUTER_MODEL")
    openrouter_max_tokens: int = 1024
    openrouter_temperature: float = 0.7

    class Config:
        env_file = str(_ENV_PATH) if _ENV_PATH.exists() else ".env"
        extra = "ignore"


settings = Settings()
