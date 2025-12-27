import logging
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.prompt import root_agent_instruction
from app.agents.state import AgentState
from app.agents.tools.search_tool import google_search
from app.config.config import get_settings
from app.infra.graph_db import get_neo4j_manager
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)
settings = get_settings()


llm = ChatGoogleGenerativeAI(
    model=settings.general_gemini_model,
    google_api_key=settings.gemini_api_key,
    temperature=0.1,
    convert_system_message_to_human=True,  # Sometimes needed for Gemini
)

# Tools
tools = [google_search]


def agent_node(state: AgentState):
    """
    The main agent node that decides the next step based on the conversation history.
    """
    messages = state["messages"]

    # Use the new prompt from app/agents/prompt.py
    system_prompt = root_agent_instruction

    # We can bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke([SystemMessage(content=system_prompt)] + list(messages))

    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["google_search", "rag_agent", "end"]:
    # ... (remains mostly the same, or we can refine logic based on prompt output)
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "google_search"

    content = str(last_message.content)
    if "rag_agent" in content or "RAG_REQUIRED" in content:
        return "rag_agent"

    return "end"


def rag_agent_node(state: AgentState):
    """
    Node to query the Neo4j Graph Database for Scrap Orders using Vector Search.
    """
    messages = state["messages"]
    last_user_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    user_query = last_user_message.content if last_user_message else ""

    neo4j = get_neo4j_manager()
    embedding_service = get_embedding_service()

    context_lines = []
    try:
        # 1. Generate Embedding for the query
        query_embedding = embedding_service.embed_query(user_query)

        # 2. Vector Search to find relevant Order nodes
        # Assuming index name "order_embeddings" exists on Order nodes
        results = neo4j.vector_search("order_embeddings", query_embedding, top_k=10)

        if not results:
            context_data = "No relevant orders found."
        else:
            # 3. For each found node, get neighborhood info (Company, ScrapType, etc.)
            for res in results:
                node = res.get("node", {})
                score = res.get("score", 0.0)

                # Fetch related info: Company, ScrapType, Address
                # matching by elementId or whatever available identifier.
                # If 'node' is a dict from neo4j driver, it might just be props.
                # simpler approach: use the node props directly + distinct
                # queries for relations if needed
                # But to get relations, we need to MATCH (n) where ID(n) ...

                # Let's assume we want to query neighbors for this specific result
                # We can use the props to identify it, or if we have an ID.
                # Ideally vector_search returns the node elementId.
                # Let's try to query neighbors using a secondary match if we have an ID property.
                order_id = node.get("id")  # App-level ID

                if order_id:
                    neighbor_query = """
                     MATCH (o:Order {id: $order_id})
                     OPTIONAL MATCH (o)-[:POSTED_BY]->(c:Company)
                     OPTIONAL MATCH (o)-[:HAS_TYPE]->(t:ScrapType)
                     OPTIONAL MATCH (o)-[:PICKUP_AT]->(a:Address)
                     RETURN c.name as company, t.name as type, a.full_address as address
                     """
                    neighbors = neo4j.execute_query(neighbor_query, {"order_id": order_id})
                    neighbor_info = neighbors[0] if neighbors else {}

                    company = neighbor_info.get("company", "Unknown")
                    scrap_type = neighbor_info.get("type", "Unknown")
                    address = neighbor_info.get("address", "Unknown")

                    order_desc = node.get("description")
                    order_qty = node.get("quantity")
                    order_price = node.get("price")
                    context_lines.append(
                        f"Order: {order_desc} | Qty: {order_qty} | "
                        f"Price: {order_price} | Type: {scrap_type} | "
                        f"Company: {company} | Loc: {address} "
                        f"(Score: {score:.2f})"
                    )
                else:
                    # Fallback if no ID
                    context_lines.append(f"Order: {node} (Score: {score:.2f})")

            context_data = "\n".join(context_lines)

    except Exception as e:
        logger.error(f"RAG Vector Search failed: {e}")
        context_data = f"Error performing search: {e}"

    return {"context": context_data}


def generate_node(state: AgentState):
    """
    Final generation node.
    """
    messages = state["messages"]
    context = state.get("context", "")

    prompt = f"""Answer the user's question based on the context provided.
    Context from Database: {context}

    If context contains order details, format them nicely (Type, Quantity, Price, Location).
    If no results found, suggest they try a different search or contact support.
    """

    response = llm.invoke([SystemMessage(content=prompt)] + list(messages))
    return {"messages": [response]}


# --- Tool Execution Node ---
tool_node = ToolNode(tools)

# --- Graph Definition ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("google_search", tool_node)
workflow.add_node("rag_agent", rag_agent_node)
workflow.add_node("generate", generate_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"google_search": "google_search", "rag_agent": "rag_agent", "end": END},
)

# After search, go back to agent or generate?
# Usually back to agent to synthesize or just generate.
workflow.add_edge("google_search", "agent")

# After RAG, go to generate
workflow.add_edge("rag_agent", "generate")
workflow.add_edge("generate", END)

# Compile
app_graph = workflow.compile()
