"""Core domain layer.

This layer contains:
- Domain entities and value objects
- Use cases (application business logic)
- Repository and service interfaces (ports)

The core is independent of infrastructure and frameworks.
"""

from app.core.domain import (
    AgentResponse,
    ChatContext,
    ChatMessage,
    Conversation,
    Message,
    User,
)
from app.core.ports import (
    IAgentOrchestrationService,
    IEmbeddingService,
    ILLMService,
)

__all__ = [
    # Domain entities
    "User",
    "Conversation",
    "Message",
    # Value objects
    "ChatContext",
    "ChatMessage",
    "AgentResponse",
    # Service ports
    "ILLMService",
    "IEmbeddingService",
    "IAgentOrchestrationService",
]
