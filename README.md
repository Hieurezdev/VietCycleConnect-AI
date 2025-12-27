# VietCycleConnect AI - Scrap Matching System

<div align="center">

**Hệ thống AI kết nối mua bán phế liệu thông minh**
*Intelligent Scrap Buyer-Seller Matching System*

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-orange.svg)](https://neo4j.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-purple.svg)](https://github.com/langchain-ai/langgraph)

</div>

---

## Tổng Quan | Overview

**VietCycleConnect AI** là một hệ thống trợ lý AI với tên gọi Anna, Anna được thiết kế để kết nối người mua và người bán phế liệu tại Việt Nam. Hệ thống sử dụng công nghệ Graph Database (Neo4j), Vector Search, và Large Language Models (LLMs) để cung cấp giải pháp tìm kiếm và ghép đôi thông minh.

**VietCycleConnect AI** is an intelligent assistant system named Anna, Anna designed to connect scrap buyers and sellers in Vietnam. The system leverages Graph Database (Neo4j), Vector Search, and Large Language Models (LLMs) to provide smart search and matching solutions.

---

## Tính Năng Chính | Key Features

### Smart Matching
- **Vector Search trên Neo4j**: Tìm kiếm đơn hàng phế liệu phù hợp nhất dựa trên độ tương đồng ngữ nghĩa (semantic similarity)
- **Embeddings 2048 chiều**: Sử dụng Google Gemini Embeddings cho độ chính xác cao

### Graph RAG (Retrieval-Augmented Generation)
- Kết hợp thông tin từ graph relationships để cung cấp câu trả lời có ngữ cảnh
- Truy xuất thông tin công ty, loại phế liệu, địa chỉ, và các mối quan hệ liên quan

### Stateless Chat API
- API chat đơn giản, hiệu năng cao, xử lý tức thời
- Response time trung bình < 3 giây

### Agentic Workflow
- Powered by **LangGraph** cho orchestration mạnh mẽ
- Tích hợp tools: Neo4j Vector Search, Text Search, và Graph Queries

---

## Kiến Trúc | Architecture

### Tech Stack

```
┌─────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                  │
│  ┌────────────────┐  ┌────────────────┐                 │
│  │  Chat Router   │  │  Health Router  │                │
│  └────────────────┘  └────────────────┘                 │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│              Application Layer (Core)                    │
│  ┌────────────────────────────────────────────────┐     │
│  │     Agent Orchestration Service (LangGraph)    │     │
│  └────────────────────────────────────────────────┘     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ LLM Service│  │ Embedding  │  │  Neo4j     │        │
│  │  (Gemini)  │  │  Service   │  │  Tools     │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│               Infrastructure Layer                       │
│  ┌────────────────┐  ┌────────────────┐                 │
│  │  Neo4j Graph   │  │  Google Gemini │                 │
│  │   Database     │  │     LLM API    │                 │
│  └────────────────┘  └────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **LangGraph Agent Orchestrator**
- Quản lý flow của conversation
- Điều phối các tools và services
- State management cho agent workflow

#### 2. **Neo4j Vector Store**
- Lưu trữ embeddings của đơn hàng phế liệu
- Vector index: `order_embeddings` (2048 dimensions)
- Graph relationships: Company, ScrapType, Location

#### 3. **Google Gemini Integration**
- **LLM Models**:
  - `gemini-2.5-pro`: General conversation
  - `gemini-3-pro-preview`: Complex reasoning
- **Embeddings**: `gemini-embedding-001` (2048D)

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Neo4j Database** (local hoặc [Neo4j Aura](https://neo4j.com/cloud/aura/))
- **Google Gemini API Key** (Get from [Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone & Setup**
   ```bash
   git clone <repository-url>
   cd VietCycleConnectAI
   make setup
   ```

2. **Configure Environment**

   Tạo file `.env`:
   ```bash
   # General
   ENV=dev
   DEBUG=true

   # LLM (Gemini)
   GEMINI_API_KEY=your_gemini_api_key_here
   THINKING_GEMINI_MODEL=gemini-3-pro-preview
   GENERAL_GEMINI_MODEL=gemini-2.5-pro

   # Neo4j Graph DB
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_neo4j_password
   ```

3. **Setup Neo4j Vector Index**

   Kết nối Neo4j và chạy Cypher:
   ```cypher
   // Create vector index for order embeddings
   CREATE VECTOR INDEX order_embeddings IF NOT EXISTS
   FOR (o:Order)
   ON o.embedding
   OPTIONS {indexConfig: {
     `vector.dimensions`: 2048,
     `vector.similarity_function`: 'cosine'
   }};
   ```

4. **Run Application**
   ```bash
   make dev
   ```

   Server sẽ chạy tại: `http://localhost:2003`

---

## API Usage

### Chat Endpoint

**Endpoint:** `POST /api/v1/chat/`

**Request:**
```json
{
  "message": "Tìm đơn mua sắt phế liệu tại Hà Nội",
}
```

**Response:**
```json
{
  "response": "Tôi tìm thấy 3 đơn hàng mua sắt phế liệu tại Hà Nội:\n\n1. Công ty TNHH ABC...",
  "agent_name": "langgraph_main",
  "processing_time_ms": 2459,
  "metadata": {}
}
```

### API Documentation

- **Swagger UI**: `http://localhost:2003/docs`
- **ReDoc**: `http://localhost:2003/redoc`

---

## Development

### Project Structure

```
VietCycleConnectAI/
├── app/
│   ├── agents/              # LangGraph agents & tools
│   │   ├── langgraph_orchestrator.py
│   │   ├── prompt.py
│   │   └── tools/
│   ├── api/                 # FastAPI routers
│   │   ├── routers/
│   │   └── dependencies.py
│   ├── core/                # Domain logic (Hexagonal Architecture)
│   │   ├── domain/          # Entities & Value Objects
│   │   └── ports/           # Service Interfaces
│   ├── infra/               # Infrastructure adapters
│   │   └── adapters/
│   ├── services/            # Business services
│   │   └── embedding_service.py
│   └── config/              # Configuration
├── tests/                   # Unit & Integration tests
├── .env                     # Environment variables
├── Makefile                 # Development commands
└── pyproject.toml          # Dependencies
```

### Available Commands

```bash
make setup          # Setup project & install dependencies
make dev            # Run development server
make test           # Run tests
make lint           # Run linter
make format         # Format code
```

---

## Technology Stack

| Category | Technology |
|----------|-----------|
| **Framework** | FastAPI 0.115+ |
| **Language** | Python 3.12+ |
| **LLM** | Google Gemini (2.5-pro, 3-pro-preview) |
| **Agent Framework** | LangGraph |
| **Database** | Neo4j 5.0+ (Graph + Vector) |
| **Embeddings** | Gemini Embedding (2048D) |
| **Package Manager** | UV |
| **Testing** | Pytest |
| **Code Quality** | Ruff, MyPy |

---

## Performance

- **Average Response Time**: < 3 seconds
- **Vector Search**: < 100ms
- **Embedding Generation**: ~500ms
- **LLM Generation**: ~2 seconds

---

## Security Notes

- Default `.env` credentials are for **development only**
- **Production**: Use environment variables, secrets management
- **Neo4j**: Enable authentication and SSL/TLS
- **API Keys**: Never commit to version control

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

This project is licensed under the MIT License.

---

## Team

Developed by **VietCycleConnect Team** and **Hieurezdev**
