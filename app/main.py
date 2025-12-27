from fastapi import FastAPI

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

    # Routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

    return app


app = create_app()
