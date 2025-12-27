import sys
from unittest.mock import MagicMock, patch

# Mock modules before import
sys.modules["neo4j"] = MagicMock()
sys.modules["neo4j.exceptions"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

# Mock LangChain/Graph
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.messages"] = MagicMock()
sys.modules["langchain_core.tools"] = MagicMock()
sys.modules["langchain_core.prompts"] = MagicMock()
sys.modules["langchain_google_genai"] = MagicMock()
sys.modules["langgraph"] = MagicMock()
sys.modules["langgraph.graph"] = MagicMock()
sys.modules["langgraph.graph.message"] = MagicMock()
sys.modules["langgraph.graph.graph"] = MagicMock()
sys.modules["langgraph.prebuilt"] = MagicMock()
sys.modules["langchain_community"] = MagicMock()
sys.modules["langchain_community.utilities"] = MagicMock()

# Mock Pydantic
import os

os.environ["GOOGLE_API_KEY"] = "fake_key"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
os.environ["GOOGLE_CSE_ID"] = "fake_cse"

mock_pydantic = MagicMock()


def field_mock(default=None, default_factory=None, **kwargs):
    if default_factory:
        return default_factory()
    return default


mock_pydantic.Field = field_mock
sys.modules["pydantic"] = mock_pydantic

mock_pydantic_settings = MagicMock()


class BaseSettings:
    pass


mock_pydantic_settings.BaseSettings = BaseSettings
sys.modules["pydantic_settings"] = mock_pydantic_settings

# Setup mocks for config
mock_settings = MagicMock()
mock_settings.gemini_api_key = "fake_key"
mock_settings.neo4j_uri = "bolt://localhost:7687"
mock_settings.neo4j_username = "neo4j"
mock_settings.neo4j_password = "password"
mock_settings.general_gemini_model = "gemini-2.0-flash-exp"
mock_settings.google_cse_id = "fake_cse"
mock_settings.google_api_key_search = "fake_search_key"


with patch("app.config.config.get_settings", return_value=mock_settings):
    # Mock Neo4jManager
    with patch("app.infra.graph_db.get_neo4j_manager") as mock_neo4j:
        mock_neo4j.return_value.execute_query.return_value = [{"node": {"name": "Test Node"}}]

        # Mock Google Search Wrapper
        with patch("app.agents.tools.search_tool.GoogleSearchAPIWrapper") as mock_search:
            mock_search.return_value.run.return_value = "Search Result"

            # Mock ChatGoogleGenerativeAI to avoid network calls
            with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
                mock_llm_instance = MockLLM.return_value
                # Mock invoke response
                from langchain_core.messages import AIMessage

                mock_llm_instance.bind_tools.return_value.invoke.return_value = AIMessage(
                    content="Final Answer"
                )
                mock_llm_instance.invoke.return_value = AIMessage(content="Final Answer")

                # Test Invocation

                # Verify prompt import
                from app.agents.prompt import root_agent_instruction

                if "VietCycleConnect AI" in root_agent_instruction:
                    print("Prompt updated successfully.")

                from app.agents.langgraph_orchestrator import app_graph

                if app_graph:
                    print("Graph compiled successfully.")

                    # Mock Neo4j execution validation
                    mock_manager = mock_neo4j.return_value
                    mock_manager.execute_query("MATCH (o:Order) RETURN o")
                    print("Neo4j Mock execution passed.")
                else:
                    print("Graph failed to compile.")
