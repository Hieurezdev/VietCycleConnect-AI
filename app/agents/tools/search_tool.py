from langchain_community.utilities import GoogleSearchAPIWrapper, SerpAPIWrapper
from langchain_core.tools import Tool, tool

from app.config.config import get_settings

settings = get_settings()


def get_search_tool() -> Tool:
    """
    Factory to create the appropriate search tool based on configuration.
    Prioritizes Google Custom Search if configured, then SerpAPI.
    """
    if settings.google_cse_id and settings.google_api_key_search:
        search = GoogleSearchAPIWrapper(
            google_api_key=settings.google_api_key_search, google_cse_id=settings.google_cse_id
        )
        return Tool(
            name="google_search",
            description="Search Google for recent results.",
            func=search.run,
        )
    elif settings.serpapi_api_key:
        search = SerpAPIWrapper(serpapi_api_key=settings.serpapi_api_key)
        return Tool(
            name="google_search",
            description="Search Google for recent results.",
            func=search.run,
        )
    else:
        # Fallback or Mock if no keys provided (prevent startup crash, but log warning)
        def mock_search(query: str) -> str:
            return "Search is not configured. Please set GOOGLE_CSE_ID/API_KEY or SERPAPI_API_KEY."

        return Tool(
            name="google_search", description="Search Google for recent results.", func=mock_search
        )


@tool
def google_search(query: str) -> str:
    """
    Search Google for recent results and information.
    Useful when you need to answer questions about current events or external knowledge.
    """
    tool_instance = get_search_tool()
    return tool_instance.run(query)
