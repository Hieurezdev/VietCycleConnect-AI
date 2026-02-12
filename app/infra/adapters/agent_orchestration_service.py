"""Agent orchestration service using LangGraph."""

import logging
import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from app.core.domain.value_objects import AgentResponse, ChatContext
from app.core.ports.services import IAgentOrchestrationService

logger = logging.getLogger(__name__)


class AgentOrchestrationService(IAgentOrchestrationService):
    """Service for orchestrating LangGraph agents."""

    def __init__(self, graph_app: Any) -> None:
        """Initialize agent orchestration service.

        Args:
            graph_app: The compiled LangGraph application.
        """
        self._graph_app = graph_app
        logger.info("AgentOrchestrationService initialized with LangGraph")

    async def route_message(self, message: str, context: ChatContext) -> AgentResponse:
        """Route message to appropriate agent and get response.

        Args:
            message: User message.
            context: Chat context (can be used to hydrate state).

        Returns:
            AgentResponse: Agent's response.
        """
        start_time = time.time()

        try:
            # Build message history from context
            history_messages = []
            for msg in context.recent_messages:
                if msg.role == "user":
                    history_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    history_messages.append(AIMessage(content=msg.content))

            # Initial State
            initial_state = {
                "messages": history_messages + [HumanMessage(content=message)],
                "context": "",
                "next_step": "",
                "output": "",
                "use_knowledge_base": context.use_knowledge_base
                if hasattr(context, "use_knowledge_base")
                else False,
            }

            # Run Graph
            result = await self._graph_app.ainvoke(initial_state)

            response_content = ""
            agent_name = "langgraph_main"

            # Extract final response from messages
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]

                # Get content - handle both attribute and property access
                try:
                    content = last_message.content
                except AttributeError as e:
                    logger.warning(f"Message has no 'content' attribute: {e}")
                    content = (
                        last_message.get("content", "") if isinstance(last_message, dict) else ""
                    )

                # Handle different content formats
                if isinstance(content, str):
                    response_content = content
                elif isinstance(content, list):
                    # Gemini returns list of content parts
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            response_content = part.get("text", "")
                            break
                        elif isinstance(part, str):
                            response_content = part
                            break
                else:
                    response_content = str(content)
                    logger.info(f"Converted to string, length: {len(response_content)}")
            else:
                logger.warning("No messages found in LangGraph result")
                logger.info(f"Result structure: {result}")

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log if we're about to use fallback error message
            if not response_content:
                logger.warning("EMPTY RESPONSE_CONTENT DETECTED! Will use fallback error message.")

            agent_response = AgentResponse(
                content=response_content or "Xin lỗi, tôi không thể xử lý yêu cầu này.",
                agent_name=agent_name,
                confidence=1.0,
                tokens_used=0,  # Usage tracking to be implemented
                processing_time_ms=processing_time_ms,
                metadata={},
            )

            logger.info(f"Message processed by LangGraph, time: {processing_time_ms}ms")

            return agent_response

        except Exception as e:
            logger.error(f"Agent orchestration failed: {e}", exc_info=True)
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Return error response
            return AgentResponse(
                content="Xin lỗi, đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại.",
                agent_name="error_handler",
                confidence=0.0,
                tokens_used=0,
                processing_time_ms=processing_time_ms,
                metadata={"error": str(e)},
            )

    async def get_agent_by_name(self, agent_name: str) -> object:
        """Get specific agent instance by name.

        Args:
            agent_name: Name of the agent.

        Returns:
            The graph application instance (LangGraph doesn't expose individual agents).
        """
        logger.info(f"get_agent_by_name called with: {agent_name}")

        return self._graph_app
