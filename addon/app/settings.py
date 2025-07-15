from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os
from functools import lru_cache
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings."""
    app_env: str = "prod"
    llm_server_url: str # URL of the LLM inference server
    llm_server_api_key: str # API key for the LLM inference server
    llm_server_proxy: str | None = None # Proxy for the LLM inference server
    model_id: str = "generic" # ID of the LLM model to use; some backends ignore this
    ha_api_url: str  # Home Assistant API URL
    ha_api_key: str  # Bearer token for Home Assistant authentication

    model_config = SettingsConfigDict(
        env_prefix="HOME_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get application settings.
    This function is cached to ensure settings are loaded only once.
    """
    load_dotenv()
    app_env = os.getenv("APP_ENV", "prod")
    if app_env == "prod":
        return Settings(
            ha_api_url="http://supervisor/core/api",
            ha_api_key=os.getenv("SUPERVISOR_TOKEN")
        ) # pyright: ignore
    else:
        return Settings() # pyright: ignore 