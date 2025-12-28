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

**VietCycleConnect AI** là một hệ thống trợ lý AI với tên gọi Tina, Tina được thiết kế để kết nối người mua và người bán phế liệu tại Việt Nam. Hệ thống sử dụng công nghệ Graph Database (Neo4j), Vector Search, và Large Language Models (LLMs) để cung cấp giải pháp tìm kiếm và ghép đôi thông minh.

**VietCycleConnect AI** is an intelligent assistant system named Tina, Tina designed to connect scrap buyers and sellers in Vietnam. The system leverages Graph Database (Neo4j), Vector Search, and Large Language Models (LLMs) to provide smart search and matching solutions.

---

## Tính Năng Chính | Key Features

### Smart Matching
- **Vector Search trên Neo4j**: Tìm kiếm đơn hàng phế liệu phù hợp nhất dựa trên độ tương đồng ngữ nghĩa (semantic similarity)
- **Embeddings**: Sử dụng Google Gemini Embeddings cho độ chính xác cao

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
- Vector index: `order_embeddings` (3072 dimensions)
- Graph relationships: Company, ScrapType, Location

#### 3. **Google Gemini Integration**
- **LLM Models**:
  - `gemini-2.5-pro`: General conversation
  - `gemini-3-pro-preview`: Complex reasoning
- **Embeddings**: `gemini-embedding-001`

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
     `vector.dimensions`: 3072,
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
| **Embeddings** | Gemini Embedding (3072D) |
| **Package Manager** | UV |
| **Testing** | Pytest |
| **Code Quality** | Ruff, MyPy |

---

## Công Nghệ & Kỹ Thuật | Technologies & Techniques

### 1. Core Technologies

#### Backend Framework
- **FastAPI**: Modern, high-performance web framework
  - Async/await support
  - Automatic API documentation (Swagger/ReDoc)
  - Pydantic data validation
  - Dependency injection system

#### Programming Language
- **Python 3.12+**: Latest Python features
  - Type hints for better code quality
  - Async programming capabilities
  - Modern syntax improvements

### 2. AI & Machine Learning

#### Large Language Models (LLMs)
- **Google Gemini 2.5-Pro**: General-purpose conversations
  - Context window: 1M tokens
  - Multimodal capabilities
- **Gemini 3-Pro-Preview**: Complex reasoning tasks
  - Advanced problem-solving
  - Chain-of-thought reasoning

#### Embeddings
- **gemini-embedding-001**: Vector embeddings
  - Dimension: 3072
  - Semantic similarity analysis
  - Multilingual support (Vietnamese optimized)

#### Agent Framework
- **LangGraph**: Stateful agent orchestration
  - Graph-based workflow management
  - Tool calling and integration
  - State persistence and recovery
  - Conditional routing logic

### 3. Database & Storage

#### Graph Database
- **Neo4j 5.0+**: High-performance graph database
  - Native graph storage
  - Cypher query language
  - ACID transactions
  - Horizontal scalability

#### Vector Search
- **Neo4j Vector Index**:
  - Cosine similarity search
  - 3072-dimensional vectors
  - Hybrid graph + vector queries
  - Real-time indexing

### 4. Architecture Patterns

#### Hexagonal Architecture (Ports & Adapters)
```
Core Domain
    ├── Entities (User, Conversation, Message)
    ├── Value Objects (ChatContext, AgentResponse)
    └── Ports (Service Interfaces)

Infrastructure
    ├── Adapters (Implementations)
    ├── Database Clients (Neo4j)
    └── External APIs (Gemini)
```

#### RAG (Retrieval-Augmented Generation)
- Vector similarity search
- Graph traversal for context enrichment
- Dynamic context construction
- Prompt engineering

### 5. Development Tools

#### Package Management
- **UV**: Ultra-fast Python package installer
  - 10-100x faster than pip
  - Lock file for reproducibility
  - Virtual environment management

#### Code Quality
- **Ruff**: Extremely fast Python linter
  - Replaces Flake8, isort, pyupgrade
  - Auto-fixes common issues
- **MyPy**: Static type checker
  - Type safety enforcement
- **Pre-commit**: Git hooks for code quality
  - Automatic formatting
  - Linting before commit

#### Testing
- **Pytest**: Modern testing framework
  - Async test support
  - Fixtures and parametrization
  - Coverage reporting

### 6. API & Integration

#### RESTful API
- **Endpoints**:
  - `POST /api/v1/chat/`: Chat interaction
  - `GET /health/`: Health check
  - `GET /docs`: Swagger UI
  - `GET /redoc`: ReDoc documentation

#### External Services
- **Google Custom Search API**: Web search capability
- **SerpAPI**: Alternative search provider
- **Neo4j Aura**: Cloud database option

### 7. Advanced Techniques

#### Semantic Search
- **Vector Embeddings**: Convert text to dense vectors
- **Cosine Similarity**: Measure semantic distance
- **Top-K Retrieval**: Get most relevant results

#### Graph Traversal
- **Relationship-based Queries**: Navigate Company → Order → ScrapType
- **Path Finding**: Discover connections
- **Aggregations**: Analytics on graph data

#### Prompt Engineering
- **System Instructions**: Role definition for AI
- **Few-shot Learning**: Examples in prompts
- **Chain-of-Thought**: Step-by-step reasoning
- **Tool Use**: Function calling for external data

#### Async Programming
- **Asyncio**: Concurrent request handling
- **Async/Await**: Non-blocking I/O
- **Connection Pooling**: Efficient resource usage

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
