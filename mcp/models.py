"""Data models for MCP Search Server.

This module contains Pydantic models for request/response validation
and data structures used throughout the application.
"""

import structlog
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from config import settings


# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer() if settings.log_format == "json"
        else structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger()


class Filters(BaseModel):
    """Optional filters for search queries."""

    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    date_from: Optional[str] = Field(None, description="Filter results from this date")
    date_to: Optional[str] = Field(None, description="Filter results until this date")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata filters")


class SearchRequest(BaseModel):
    """Search request model matching the search service API."""

    query: str = Field(..., min_length=1, description="Search query text")
    user_id: str = Field(..., min_length=1, description="User identifier")
    indices: List[str] = Field(..., min_length=1, description="List of OpenSearch indices to search")
    filters: Optional[Filters] = Field(None, description="Optional search filters")

    @field_validator('indices')
    @classmethod
    def validate_indices(cls, v: List[str]) -> List[str]:
        """Validate that indices list is not empty and contains valid values."""
        if not v:
            raise ValueError("At least one index must be specified")
        if any(not idx.strip() for idx in v):
            raise ValueError("Index names cannot be empty or whitespace")
        return v


class SearchResult(BaseModel):
    """Individual search result."""

    id: str = Field(..., description="Document ID")
    score: float = Field(..., description="Relevance score")
    source: Dict[str, Any] = Field(..., description="Document source data")
    index: str = Field(..., description="Index name where document was found")
    highlights: Optional[Dict[str, List[str]]] = Field(None, description="Highlighted text snippets")


class SearchResponse(BaseModel):
    """Search response model matching the search service API."""

    results: List[SearchResult] = Field(default_factory=list, description="List of search results")
    query_expanded: str = Field(..., description="Query expanded with synonyms")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    request_id: str = Field(..., description="Unique request identifier")
