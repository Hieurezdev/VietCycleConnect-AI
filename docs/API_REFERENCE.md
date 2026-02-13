# API Reference: VietCycleConnect AI

**Version**: 1.0.0
**Status**: Production Ready

## Overview

The VietCycleConnect AI API provides a unified interface for the "Tina" intelligent assistant. It supports two primary modes of operation via a single endpoint:
1.  **Knowledge Base RAG**: For answering questions about website usage, legal policies, and general support.
2.  **Scrap Matching (Graph RAG)**: For finding and matching scrap buy/sell orders based on semantic similarity and graph relationships.

## Base URLs

-   **Development**: `http://localhost:8000/api/v1`
-   **Production**: `https://vietcycleconnect-ai-production.up.railway.app/api/v1`

---

## Endpoint: Chat Completion

**URL**: `/chat/`
**Method**: `POST`
**Content-Type**: `application/json`

### Request Schema

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `message` | string | Yes | - | The user's query or input text. |
| `use_knowledge_base` | boolean | No | `false` | **Mode Switch**. Set `true` for general support/legal Q&A. Set `false` for scrap order matching. |
| `conversation_id` | UUID | No | `null` | Optional ID to track conversation context. |
| `messages` | array | No | `[]` | List of previous message history objects (for context). |

### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | The AI's generated response (markdown formatted). |
| `agent_name` | string | The internal agent that handled the request (e.g., `rag_knowledge_agent`, `rag_scraptype_agent`). |
| `processing_time_ms` | integer | Execution time in milliseconds. |
| `metadata` | object | Additional debug info or context. |

---

## Usage Modes

### Mode 1: Knowledge Base (`use_knowledge_base: true`)

**Use Case**: User asks "How to register?", "Privacy Policy?", "Contact support?".
**Behavior**: Queries MongoDB Atlas Vector Store for relevant documentation.

**Request:**
```bash
curl -X POST https://vietcycleconnect-ai-production.up.railway.app/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Làm sao để đăng ký tài khoản?",
    "use_knowledge_base": true
  }'
```

**Response Example:**
```json
{
  "response": "Chào bạn,\n\nĐể đăng ký tài khoản, bạn vui lòng làm theo các bước sau:...\n",
  "agent_name": "rag_knowledge_agent",
  "processing_time_ms": 1200,
  "metadata": {}
}
```

### Mode 2: Scrap Matching (`use_knowledge_base: false`)

**Use Case**: User asks "Find iron scrap orders", "Buy PET plastic in Hanoi".
**Behavior**: Queries Neo4j Graph Database using Vector Search + Graph Traversal.
**Output Format**: Returns a list of **Order IDs** only (optimized for frontend parsing).

**Request:**
```bash
curl -X POST https://vietcycleconnect-ai-production.up.railway.app/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tìm đơn hàng sắt vụn",
    "use_knowledge_base": false
  }'
```

**Response Example:**
```json
{
  "response": "Tìm thấy các đơn hàng phù hợp sau đây:\n- ORDER-123\n- ORDER-456\n- ORDER-789",
  "agent_name": "rag_scraptype_agent",
  "processing_time_ms": 2500,
  "metadata": {}
}
```
