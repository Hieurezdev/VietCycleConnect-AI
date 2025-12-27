"""Domain entities for the VietCycleConnect AI system.

Entities are objects with identity that persist over time.
They represent the core business concepts.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    """User entity representing a system user."""

    id: UUID = Field(default_factory=uuid4)
    email: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class Conversation(BaseModel):
    """Conversation entity representing a chat session."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class Message(BaseModel):
    """Message entity representing a single message in a conversation."""

    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    agent_name: str | None = None  # Which agent handled this message
    tokens_used: int | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True
