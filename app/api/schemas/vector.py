"""Pydantic schemas for vector store API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkCreate(BaseModel):
    """Schema for creating a new knowledge chunk."""

    content: str = Field(..., description="Main content of the knowledge chunk")
    headers: list[str] = Field(default_factory=list, description="List of headers or metadata")
    summary: str = Field(default="", description="Brief summary of the content")
    keywords: list[str] = Field(default_factory=list, description="List of keywords")
    type: str = Field(default="", description="Type/category of the chunk")


class ChunkUpdate(BaseModel):
    """Schema for updating an existing knowledge chunk."""

    content: str | None = Field(None, description="New content")
    headers: list[str] | None = Field(None, description="New headers")
    summary: str | None = Field(None, description="New summary")
    keywords: list[str] | None = Field(None, description="New keywords")
    type: str | None = Field(None, description="New type/category")


class ChunkResponse(BaseModel):
    """Schema for knowledge chunk response."""

    uuid: UUID = Field(..., description="Unique identifier")
    headers: list[str] = Field(..., description="Headers or metadata")
    content: str = Field(..., description="Main content")
    summary: str = Field(..., description="Summary")
    keywords: list[str] = Field(..., description="Keywords")
    type: str = Field(..., description="Type/category")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class ChunkSearchQuery(BaseModel):
    """Schema for searching knowledge chunks."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=5, ge=1, le=100, description="Maximum number of results")
    type: str | None = Field(None, description="Filter by chunk type")
    similarity_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1)",
    )


class ChunkSearchResult(BaseModel):
    """Schema for search result with similarity score."""

    chunk: ChunkResponse = Field(..., description="Knowledge chunk data")
    similarity: float = Field(..., description="Similarity score (0-1)")


class ChunkListQuery(BaseModel):
    """Schema for listing knowledge chunks."""

    type: str | None = Field(None, description="Filter by chunk type")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class ChunkListResponse(BaseModel):
    """Schema for list of knowledge chunks."""

    chunks: list[ChunkResponse] = Field(..., description="List of knowledge chunks")
    total: int = Field(..., description="Total number of chunks matching filter")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")


class ChunkBatchCreate(BaseModel):
    """Schema for batch creating knowledge chunks."""

    chunks: list[ChunkCreate] = Field(
        ..., min_length=1, max_length=100, description="List of chunks to create (max 100)"
    )


class ChunkBatchResponse(BaseModel):
    """Schema for batch creation response."""

    chunks: list[ChunkResponse] = Field(..., description="Created knowledge chunks")
    count: int = Field(..., description="Number of chunks created")
