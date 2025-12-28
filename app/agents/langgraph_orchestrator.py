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


def should_continue(state: AgentState) -> Literal["google_search", "rag_agent", "end"]:
    """
    Determine the next step based on the agent's response.

    Priority:
    1. If LLM called a tool -> execute that tool
    2. If response is a final answer -> end
    3. Never loop back to agent after getting a response
    """
    messages = state["messages"]
    last_message = messages[-1]

    logger.info("=== should_continue called ===")
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
        logger.info(
            f"Starts with [RAG_REQUIRED]: {actual_text.strip().startswith('[RAG_REQUIRED]')}"
        )

        if actual_text.strip().startswith("[RAG_REQUIRED]"):
            logger.info("Decision: Routing to rag_agent (RAG marker detected)")
            return "rag_agent"

    logger.info("Decision: Routing to END (default)")
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
                    neighbor_query = """
                     MATCH (o:Order {id: $order_id})
                     OPTIONAL MATCH (o)-[:POSTED_BY]->(c:Company)
                     OPTIONAL MATCH (o)-[:HAS_TYPE]->(t:ScrapType)
                     OPTIONAL MATCH (o)-[:PICKUP_AT]->(a:Address)
                     RETURN c.name as company, t.name as type, a.full_address as address,
                            c.description as company_desc, a.type as address_type,
                            c.phone as phone, c.tax_code as tax_code,
                            c.email as email, c.verification_status as verification_status,
                            a.description as address_desc,
                            o.quantity as quantity, t.unit as unit, t.is_raw as is_raw,
                            o.price as price, o.vehicle_req as vehicle_req,
                            o.description as order_desc
                     """
                    neighbors = neo4j.execute_query(neighbor_query, {"order_id": order_id})
                    neighbor_info = neighbors[0] if neighbors else {}

                    company_name = neighbor_info.get("company", "Unknown")
                    scrap_type = neighbor_info.get("type", "Unknown")
                    address = neighbor_info.get("address", "Unknown")
                    unit = neighbor_info.get("unit", "Unknown")
                    phone = neighbor_info.get("phone", "Unknown")
                    tax_code = neighbor_info.get("tax_code", "Unknown")
                    address_description = neighbor_info.get("address_desc", "Unknown")
                    is_raw = neighbor_info.get("is_raw", "Unknown")
                    email = neighbor_info.get("email", "Unknown")
                    verification_status = neighbor_info.get("verification_status", "Unknown")
                    company_desc = neighbor_info.get("company_desc", "Unknown")
                    address_type = neighbor_info.get("address_type", "Unknown")
                    order_description = neighbor_info.get("order_desc", "Unknown")
                    vehicle_req = neighbor_info.get("vehicle_req", "Unknown")
                    order_qty = neighbor_info.get("quantity")
                    order_price = neighbor_info.get("price")

                    context_lines.append(
                        f"Company: {company_name} | "
                        f"Type: {scrap_type} | "
                        f"Qty: {order_qty} | "
                        f"Price: {order_price} | "
                        f"Address: {address} | "
                        f"Phone: {phone} | "
                        f"Tax Code: {tax_code} | "
                        f"Unit: {unit} | "
                        f"Order Description: {order_description} | "
                        f"Address Description: {address_description} | "
                        f"Vehicle Required: {vehicle_req} | "
                        f"Is Raw: {is_raw} | "
                        f"Email: {email} | "
                        f"Verification Status: {verification_status} | "
                        f"Company Description: {company_desc} | "
                        f"Address Type: {address_type} | "
                        f"(Score: {score:.2f})"
                    )
                else:
                    context_lines.append(f"Order: {node} (Score: {score:.2f})")

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

    # Create system prompt with context
    system_prompt = f"""You are Tina, a cute assistant of scrap matching system.

Based on the following search results from our database, provide a helpful response in Vietnamese:

{context}

**IMPORTANT**: Format your response as a markdown list with the following structure:

1. Start with a brief greeting and summary of how many results were found
2. For each order, create a numbered list item with:
   - **Công ty**: Company name
   - **Loại phế liệu**: Scrap type
   - **Số lượng**: Quantity with unit
   - **Giá**: Price (or "Liên hệ" if not specified)
   - **Địa chỉ**: Full address
   - **Số điện thoại**: Phone number (or "Chưa cập nhật" if not available)
   - **Email**: Email (or "Chưa cập nhật" if not available)
   - **Trạng thái xác minh**: Verification status if available
   - **Yêu cầu phương tiện**: Vehicle requirements if specified
   - **Đơn vị**: Unit if available
   - **Loại đơn hàng**: Order type if available
   - **Raw**: Raw if available
   - **Mô tả đơn hàng**: Brief description from order
   - **Mô tả địa chỉ**: Brief description from address
   - **Mô tả công ty**: Brief description from company

3. End with a helpful call-to-action

Example format:
```
Xin chào! Tôi tìm thấy [số lượng] đơn hàng phù hợp với yêu cầu của bạn:

### 1. [Tên công ty]
- **Loại phế liệu**: [loại]
- **Số lượng**: [số lượng] [đơn vị]
- **Giá**: [giá] VNĐ
- **Địa chỉ**: [địa chỉ đầy đủ]
- **Số điện thoại**: [số điện thoại]
- **Email**: [email]
- **Mô tả**: [mô tả ngắn gọn]
- **Trạng thái xác minh**: [trạng thái xác minh]
- **Yêu cầu phương tiện**: [yêu cầu phương tiện]
- **Đơn vị**: [đơn vị]
- **Loại đơn hàng**: [loại đơn hàng]
- **Raw**: [raw]
- **Mô tả đơn hàng**: [mô tả đơn hàng]
- **Mô tả địa chỉ**: [mô tả địa chỉ]
- **Mô tả công ty**: [mô tả công ty]

### 2. [Tên công ty tiếp theo]
...
```

If no results found, politely suggest they try different search terms or contact support.
"""

    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_query)])

    return {"messages": [response]}


tool_node = ToolNode(tools)

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


workflow.add_edge("google_search", "agent")


workflow.add_edge("rag_agent", "generate")
workflow.add_edge("generate", END)


app_graph = workflow.compile()
