import os
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    env: str = os.getenv("ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    # Models
    thinking_gemini_model: str = "gemini-3-pro-preview"
    general_gemini_model: str = "gemini-2.5-pro"
    embedding_model: str = "gemini-embedding-001"

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        if not hasattr(self, "_llm"):
            self._llm = ChatGoogleGenerativeAI(
                model=self.general_gemini_model,
                google_api_key=self.gemini_api_key,
                temperature=0.2,
                convert_system_message_to_human=True,
                max_tokens=4096,
            )
        return self._llm

    @property
    def gemini_model(self) -> str:
        return self.general_gemini_model

    @property
    def rag_model(self) -> str:
        return self.general_gemini_model

    # --- Neo4j Settings ---
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_username: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")

    # --- Agent Settings ---
    google_search_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    google_cse_id: str | None = os.getenv("GOOGLE_CSE_ID")
    serpapi_api_key: str | None = os.getenv("SERPAPI_API_KEY")

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
