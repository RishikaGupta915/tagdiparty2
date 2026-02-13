from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = Field(default="Nexus AI")
    env: str = Field(default="dev")
    database_url: str = Field(default="sqlite:///./data/app.db", validation_alias="DATABASE_URL")
    cors_origins: str = Field(default="http://localhost:5173", validation_alias="CORS_ORIGINS")
    maintenance_enabled: bool = Field(default=True, validation_alias="MAINTENANCE_ENABLED")
    maintenance_interval_minutes: int = Field(default=15, validation_alias="MAINTENANCE_INTERVAL_MINUTES")

    nl2sql_mode: str = Field(default="llm", validation_alias="NL2SQL_MODE")
    llm_provider: str = Field(default="gemini", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(default="gemini-2.0-flash", validation_alias="LLM_MODEL")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
