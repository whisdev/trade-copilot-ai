from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# .env next to backend/ folder (parent of app/)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH, override=False)


class Settings(BaseSettings):
    chutes_api_key: str = Field(default="", validation_alias="CHUTES_API_KEY")
    database_url: str = "sqlite+aiosqlite:///./chat.db"
    chutes_base_url: str = "https://llm.chutes.ai/v1"
    chutes_model: str = "Qwen/Qwen3-32B"
    chutes_max_tokens: int = 1024
    chutes_temperature: float = 0.7

    class Config:
        env_file = str(_ENV_PATH) if _ENV_PATH.exists() else ".env"
        extra = "ignore"


settings = Settings()
