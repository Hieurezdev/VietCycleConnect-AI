from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import chat, health
from app.config.config import Settings
from app.config.logging import configure_logging


def create_app() -> FastAPI:
    settings = Settings()  # reads env once
    configure_logging(settings)

    app = FastAPI(
        title="VietCycleConnect AI - Scrap Matching System",
        description=(
            "AI-powered assistant for matching scrap buyers and sellers using LangGraph and Neo4j"
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS Configuration
    # Allow all origins for testing purposes (using regex to support credentials)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

    return app


app = create_app()
