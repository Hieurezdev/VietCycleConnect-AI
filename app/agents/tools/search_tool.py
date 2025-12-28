from googleapiclient.discovery import build
from langchain_core.tools import Tool, tool

from app.config.config import get_settings

settings = get_settings()


def get_search_tool() -> Tool:
    """
    Factory to create the appropriate search tool based on configuration.
    Uses Google Custom Search API.
    """

    def search_google(query: str) -> str:
        """Execute Google Custom Search."""
        if not settings.google_cse_id or not settings.gemini_api_key:
            raise ValueError(
                "Search is not configured. Please set GOOGLE_CSE_ID and GEMINI_API_KEY."
            )

        try:
            service = build("customsearch", "v1", developerKey=settings.gemini_api_key)
            result = service.cse().list(q=query, cx=settings.google_cse_id, num=5).execute()

            items = result.get("items", [])

            if not items:
                raise ValueError(f"No search results found for: {query}")

            # Format results as string
            results = []
            for i, item in enumerate(items, 1):
                results.append(
                    f"{i}. {item.get('title', 'No title')}\n"
                    f"   Link: {item.get('link', 'N/A')}\n"
                    f"   Snippet: {item.get('snippet', 'No description')}\n"
                )

            return "\n".join(results)

        except Exception as e:
            raise ValueError(f"Google search failed: {str(e)}") from None

    return Tool(
        name="google_search",
        description=(
            "Search Google for recent results and information. "
            "Useful for current events, market prices, general knowledge."
        ),
        func=search_google,
    )


@tool
def google_search(query: str) -> str:
    """
    Search Google for recent results and information.
    Useful when you need to answer questions about current events or external knowledge.

    Args:
        query: The search query string

    Returns:
        str: Formatted search results or error message
    """
    tool_instance = get_search_tool()
    return tool_instance.run(query)
