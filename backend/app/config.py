from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# .env next to backend/ folder (parent of app/)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH, override=False)


class Settings(BaseSettings):
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_api_keys: str = Field(default="", validation_alias="OPENAI_API_KEYS")
    mongodb_url: str = Field(default="mongodb://localhost:27017", validation_alias="MONGODB_URL")
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_max_tokens: int = 1024
    openai_temperature: float = 0.7

    def get_openai_key_list(self) -> list[str]:
        """Return list of API keys. OPENAI_API_KEYS (comma-separated) takes precedence over OPENAI_API_KEY."""
        keys_str = (self.openai_api_keys or "").strip()
        if keys_str:
            return [k.strip() for k in keys_str.split(",") if k.strip()]
        single = (self.openai_api_key or "").strip()
        return [single] if single else []

    class Config:
        env_file = str(_ENV_PATH) if _ENV_PATH.exists() else ".env"
        extra = "ignore"


settings = Settings()
