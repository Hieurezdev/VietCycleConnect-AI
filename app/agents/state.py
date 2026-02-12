from collections.abc import Sequence
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """The state of the agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    next_step: str  # "search", "rag", "respond"
    output: str
    use_knowledge_base: bool  # Mode flag: True for knowledge base, False for scrap matching
