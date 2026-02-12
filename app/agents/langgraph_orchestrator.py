import logging
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.prompt import root_agent_instruction
from app.agents.state import AgentState
from app.agents.tools.search_tool import google_search
from app.config.config import get_settings
from app.infra.graph_db import get_neo4j_manager
from app.infra.mongodb import get_mongodb_manager
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)
settings = get_settings()
llm = settings.llm

tools = [google_search]


def agent_node(state: AgentState):
    """
    The main agent node that decides the next step based on the conversation history.
    """
    messages = state["messages"]

    # Use the prompt from app/agents/prompt.py
    system_prompt = root_agent_instruction

    # We can bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke([SystemMessage(content=system_prompt)] + list(messages))

    return {"messages": [response]}


def should_continue(
    state: AgentState,
) -> Literal[
    "google_search",
    "rag_knowledge_agent",
    "rag_scraptype_agent",
    "rag_address_agent",
    "rag_company_agent",
    "rag_order_agent",
    "end",
]:
    """
    Determine the next step based on the agent's response.

    Priority:
    1. If LLM called a tool -> execute that tool
    2. If response contains a RAG marker -> route to appropriate RAG agent
    5. If response is a final answer -> end
    """
    messages = state["messages"]
    last_message = messages[-1]

    logger.info("=== should_continue called ===")

    # Check if knowledge base mode is enabled (passed from API -> State)
    if state.get("use_knowledge_base", False):
        logger.info("Decision: Routing to rag_knowledge_agent (knowledge base mode)")
        return "rag_knowledge_agent"

    logger.info(f"Last message type: {type(last_message)}")

    # Check if there are tool calls to execute
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Tool was called - execute it
        logger.info("Decision: Routing to google_search (tool call)")
        return "google_search"

    if hasattr(last_message, "content"):
        content = last_message.content

        actual_text = ""
        if isinstance(content, str):
            actual_text = content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    actual_text = part.get("text", "")
                    break

        logger.info(f"Extracted text: {repr(actual_text)[:200]}")

        # Check for specific RAG markers
        if actual_text.strip().startswith("[RAG_SCRAPTYPE]"):
            logger.info("Decision: Routing to rag_scraptype_agent (ScrapType search)")
            return "rag_scraptype_agent"
        elif actual_text.strip().startswith("[RAG_ADDRESS]"):
            logger.info("Decision: Routing to rag_address_agent (Address search)")
            return "rag_address_agent"
        elif actual_text.strip().startswith("[RAG_COMPANY]"):
            logger.info("Decision: Routing to rag_company_agent (Company search)")
            return "rag_company_agent"
        elif actual_text.strip().startswith("[RAG_ORDER]"):
            logger.info("Decision: Routing to rag_order_agent (Order search)")
            return "rag_order_agent"

    logger.info("Decision: Routing to END (default)")
    return "end"


def rag_knowledge_agent_node(state: AgentState):
    """
    Node to query knowledge base from MongoDB Atlas using Vector Search.
    For website usage guides and legal information.
    """
    messages = state["messages"]
    last_user_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    user_query = last_user_message.content if last_user_message else ""

    mongo = get_mongodb_manager()
    embedding_service = get_embedding_service()

    context_data = ""
    try:
        query_embedding = embedding_service.embed_query(user_query)

        # Search specifically for usage guides and legal docs
        results = mongo.vector_search(query_embedding, top_k=5)

        if not results:
            context_data = "KHÔNG TÌM THẤY THÔNG TIN TRONG CƠ SỞ DỮ LIỆU."
        else:
            context_lines = []
            for res in results:
                title = res.get("title", "Untitled")
                content = res.get("content", "")
                category = res.get("category", "General")
                score = res.get("score", 0.0)

                context_lines.append(
                    f"--- Document (Score: {score:.2f}) ---\n"
                    f"Title: {title}\nCategory: {category}\nContent:\n{content}\n"
                )

            context_data = "\n".join(context_lines)

    except Exception as e:
        logger.error(f"MongoDB Vector Search failed: {e}", exc_info=True)
        context_data = f"Error performing search: {e}"

    logger.info(f"Knowledge Base Context built: {len(context_data)} chars")
    return {"context": context_data}


def rag_scraptype_agent_node(state: AgentState):
    """
    Node to query scrap type from the Neo4j Graph Database for Scrap Orders using Vector Search.
    """
    messages = state["messages"]
    last_user_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    user_query = last_user_message.content if last_user_message else ""

    neo4j = get_neo4j_manager()
    embedding_service = get_embedding_service()

    context_lines = []
    try:
        query_embedding = embedding_service.embed_query(user_query)

        results = neo4j.vector_search("scraptype_embedding_index", query_embedding, top_k=5)

        if not results:
            context_data = "No relevant scrap types found."
        else:
            for res in results:
                node = res.get("node", {})
                score = res.get("score", 0.0)

                scrap_type_id = node.get("id")  # App-level ID
                scrap_type = node.get("name", "Unknown")
                logging.info(f"Scrap Type ID: {scrap_type_id}")
                if scrap_type_id:
                    # Find orders associated with this scrap type and return only their IDs
                    neighbor_query = """
                     MATCH (t:ScrapType {id: $scrap_type_id})
                     OPTIONAL MATCH (o:Order)-[:HAS_TYPE]->(t)
                     RETURN o.id as order_id
                     LIMIT 20
                     """
                    neighbors = neo4j.execute_query(
                        neighbor_query, {"scrap_type_id": scrap_type_id}
                    )

                    if neighbors:
                        for row in neighbors:
                            order_id = row.get("order_id")
                            if order_id:
                                context_lines.append(
                                    f"Order ID: {order_id} "
                                    f"(Match: {scrap_type} - Score: {score:.2f})"
                                )
                else:
                    context_lines.append(f"Scrap Type Found: {node} (Score: {score:.2f})")

            context_data = "\n".join(context_lines)

    except Exception as e:
        logger.error(f"RAG Vector Search failed: {e}", exc_info=True)
        context_data = f"Error performing search: {e}"

    logger.info(f"RAG Agent Context built: {len(context_data)} chars")
    logger.debug(f"Context preview: {context_data[:200]}")
    return {"context": context_data}


def rag_address_agent_node(state: AgentState):
    """
    Node to query address from the Neo4j Graph Database for Scrap Orders using Vector Search.
    """
    messages = state["messages"]
    last_user_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    user_query = last_user_message.content if last_user_message else ""

    neo4j = get_neo4j_manager()
    embedding_service = get_embedding_service()

    context_lines = []
    try:
        query_embedding = embedding_service.embed_query(user_query)

        results = neo4j.vector_search("address_embedding_index", query_embedding, top_k=5)

        if not results:
            context_data = "No relevant addresses found."
        else:
            for res in results:
                node = res.get("node", {})
                score = res.get("score", 0.0)

                address_id = node.get("id")  # App-level ID
                logging.info(f"Address ID: {address_id}")
                if address_id:
                    # Find orders associated with this address and return only their IDs
                    neighbor_query = """
                     MATCH (a:Address {id: $address_id})
                     OPTIONAL MATCH (o:Order)-[:PICKUP_AT]->(a)
                     RETURN o.id as order_id
                     LIMIT 20
                     """
                    neighbors = neo4j.execute_query(neighbor_query, {"address_id": address_id})

                    if neighbors:
                        for row in neighbors:
                            order_id = row.get("order_id")
                            if order_id:
                                context_lines.append(
                                    f"Order ID: {order_id} (Address Match - Score: {score:.2f})"
                                )
                else:
                    context_lines.append(f"Address Match: {node} (Score: {score:.2f})")

            context_data = "\n".join(context_lines)

    except Exception as e:
        logger.error(f"RAG Vector Search failed: {e}", exc_info=True)
        context_data = f"Error performing search: {e}"

    logger.info(f"RAG Agent Context built: {len(context_data)} chars")
    logger.debug(f"Context preview: {context_data[:200]}")
    return {"context": context_data}


def rag_company_agent_node(state: AgentState):
    """
    Node to query company from the Neo4j Graph Database for Scrap Orders using Vector Search.
    """
    messages = state["messages"]
    last_user_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    user_query = last_user_message.content if last_user_message else ""

    neo4j = get_neo4j_manager()
    embedding_service = get_embedding_service()

    context_lines = []
    try:
        query_embedding = embedding_service.embed_query(user_query)

        results = neo4j.vector_search("company_embedding_index", query_embedding, top_k=5)

        if not results:
            context_data = "No relevant companies found."
        else:
            for res in results:
                node = res.get("node", {})
                score = res.get("score", 0.0)

                company_id = node.get("id")  # App-level ID
                logging.info(f"Company ID: {company_id}")
                if company_id:
                    # Find orders associated with this company and return only their IDs
                    neighbor_query = """
                     MATCH (c:Company {id: $company_id})
                     OPTIONAL MATCH (o:Order)-[:POSTED_BY]->(c)
                     RETURN o.id as order_id
                     LIMIT 20
                     """
                    neighbors = neo4j.execute_query(neighbor_query, {"company_id": company_id})

                    if neighbors:
                        for row in neighbors:
                            order_id = row.get("order_id")
                            if order_id:
                                context_lines.append(
                                    f"Order ID: {order_id} (Company Match - Score: {score:.2f})"
                                )
                else:
                    context_lines.append(f"Company Match: {node} (Score: {score:.2f})")

            context_data = "\n".join(context_lines)

    except Exception as e:
        logger.error(f"RAG Vector Search failed: {e}", exc_info=True)
        context_data = f"Error performing search: {e}"

    logger.info(f"RAG Agent Context built: {len(context_data)} chars")
    logger.debug(f"Context preview: {context_data[:200]}")
    return {"context": context_data}


def rag_order_agent_node(state: AgentState):
    """
    Node to query order from the Neo4j Graph Database for Scrap Orders using Vector Search.
    """
    messages = state["messages"]
    last_user_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    user_query = last_user_message.content if last_user_message else ""

    neo4j = get_neo4j_manager()
    embedding_service = get_embedding_service()

    context_lines = []
    try:
        query_embedding = embedding_service.embed_query(user_query)

        results = neo4j.vector_search("order_embedding_index", query_embedding, top_k=5)

        if not results:
            context_data = "No relevant orders found."
        else:
            for res in results:
                node = res.get("node", {})
                score = res.get("score", 0.0)

                order_id = node.get("id")  # App-level ID
                logging.info(f"Order ID: {order_id}")
                if order_id:
                    context_lines.append(
                        f"Order ID: {order_id} (Direct Match - Score: {score:.2f})"
                    )
                else:
                    context_lines.append(f"Order Match: {node} (Score: {score:.2f})")

            context_data = "\n".join(context_lines)

    except Exception as e:
        logger.error(f"RAG Vector Search failed: {e}", exc_info=True)
        context_data = f"Error performing search: {e}"

    logger.info(f"RAG Agent Context built: {len(context_data)} chars")
    logger.debug(f"Context preview: {context_data[:200]}")
    return {"context": context_data}


def generate_node(state: AgentState):
    """
    Final generation node.
    """
    messages = state["messages"]
    context = state.get("context", "")

    user_query = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break

    logger.info(f"User query: {user_query[:100]}")

    logger.info(f"User query: {user_query[:100]}")

    # Check mode to determine system prompt
    is_knowledge_base_mode = state.get("use_knowledge_base", False)

    if is_knowledge_base_mode:
        # Knowledge Base Prompt
        system_prompt = f"""Bạn là trợ lý AI của VietCycleConnect,
chuyên hỗ trợ giải đáp về cách sử dụng website
và các vấn đề pháp lý.

Dựa trên các thông tin được tìm thấy trong CƠ SỞ TRI THỨC dưới đây,
hãy trả lời câu hỏi của người dùng
một cách chính xác, thân thiện và hữu ích.

CƠ SỞ TRI THỨC:
{context}

HƯỚNG DẪN TRẢ LỜI:
1. Chỉ sử dụng thông tin có trong CƠ SỞ TRI THỨC để trả lời. Nếu không tìm thấy thông tin phù hợp,
hãy xin lỗi và gợi ý liên hệ hotline hỗ trợ.
2. Trình bày câu trả lời rõ ràng, dễ hiểu, sử dụng các bước (1, 2, 3...) hoặc gạch đầu dòng
nếu là hướng dẫn quy trình.
3. Giữ giọng văn chuyên nghiệp nhưng gần gũi (dùng "mình", "bạn" hoặc "chúng tôi").
4. Cuối câu trả lời có thể gợi ý thêm các mục liên quan nếu có.
"""
    else:
        # Existing Scrap Matching Prompt (Modified for ID Only)
        system_prompt = f"""You are Tina, a cute assistant of scrap matching system.

Based on the following search results from our database, specifically the found Order IDs,
provide a response in Vietnamese that lists the relevant Order IDs.

Search Results:
{context}

**IMPORTANT**:
Your task is to extracting the 'Order ID' values from the search results
and present them in a clear list.
Do NOT invent details. If the context contains IDs, just list them.

Format your response as:
"Tìm thấy các đơn hàng phù hợp sau đây:"
- [Order ID 1]
- [Order ID 2]
...

If no IDs are found in the context, say "Không tìm thấy đơn hàng nào phù hợp."
"""

    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_query)])

    return {"messages": [response]}


tool_node = ToolNode(tools)

workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("google_search", tool_node)
workflow.add_node("rag_knowledge_agent", rag_knowledge_agent_node)
workflow.add_node("rag_scraptype_agent", rag_scraptype_agent_node)
workflow.add_node("rag_address_agent", rag_address_agent_node)
workflow.add_node("rag_company_agent", rag_company_agent_node)
workflow.add_node("rag_order_agent", rag_order_agent_node)
workflow.add_node("generate", generate_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "google_search": "google_search",
        "rag_knowledge_agent": "rag_knowledge_agent",
        "rag_scraptype_agent": "rag_scraptype_agent",
        "rag_address_agent": "rag_address_agent",
        "rag_company_agent": "rag_company_agent",
        "rag_order_agent": "rag_order_agent",
        "end": END,
    },
)

workflow.add_edge("google_search", "agent")

# Connect all RAG nodes to generate
workflow.add_edge("rag_knowledge_agent", "generate")
workflow.add_edge("rag_scraptype_agent", "generate")
workflow.add_edge("rag_address_agent", "generate")
workflow.add_edge("rag_company_agent", "generate")
workflow.add_edge("rag_order_agent", "generate")
workflow.add_edge("generate", END)


app_graph = workflow.compile()
