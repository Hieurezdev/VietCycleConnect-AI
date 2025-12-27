"""Value objects for the VietCycleConnect AI system.

Value objects are immutable objects defined by their attributes.
They have no identity and are interchangeable.
"""

from pydantic import BaseModel, Field


class EmbeddingVector(BaseModel):
    """Value object representing an embedding vector."""

    values: list[float]
    dimension: int = 3072  # gemini-embedding-001
    model: str = "gemini-embedding-001"

    def model_post_init(self, __context: object) -> None:
        """Validate embedding dimension after model initialization."""
        if len(self.values) != self.dimension:
            raise ValueError(
                f"Embedding dimension must be {self.dimension}, got {len(self.values)}"
            )

    class Config:
        """Pydantic config."""

        frozen = True


class ChatMessage(BaseModel):
    """Value object for a chat message."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str

    class Config:
        frozen = True


class ChatContext(BaseModel):
    """Value object representing conversation context."""

    recent_messages: list[ChatMessage] = Field(default_factory=list)
    detected_topics: list[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        frozen = True


class AgentResponse(BaseModel):
    """Value object representing an agent's response."""

    content: str
    agent_name: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    tokens_used: int = 0
    processing_time_ms: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        frozen = True


class SearchQuery(BaseModel):
    """Value object for RAG search queries."""

    query_text: str
    embedding: EmbeddingVector | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, str] = Field(default_factory=dict)
    min_relevance_score: float = Field(default=0.7, ge=0.0, le=1.0)

    class Config:
        """Pydantic config."""

        frozen = True


class RetrievedDocument(BaseModel):
    """Value object for retrieved documents from RAG."""

    document_id: str
    content: str
    title: str | None = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    source: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        frozen = True
