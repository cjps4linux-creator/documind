from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = "DocuMind"
    OPENAI_API_KEY: str | None = Field(default=None)
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    OPENAI_CHAT_MODEL: str = Field(default="gpt-4o-mini")
    BEDROCK_EMBEDDING_MODEL_ID: str = Field(default="amazon.titan-embed-text-v2:0")
    BEDROCK_CHAT_MODEL_ID: str = Field(default="anthropic.claude-3-5-sonnet-20240620-v1:0")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./documind.db")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1")
    EMBEDDING_DIM: int = Field(default=1536)
    CHUNK_SIZE: int = Field(default=512)
    CHUNK_OVERLAP: int = Field(default=64)
settings = Settings()
