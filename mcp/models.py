"""Data models for MCP Search Server.

This module contains Pydantic models for request/response validation
and data structures used throughout the application.
"""

import structlog
from datetime import datetime
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


class DateRange(BaseModel):
    """Date range filter for search."""
    from_date: str = Field(..., alias="from", description="Start date in ISO format")
    to_date: str = Field(..., alias="to", description="End date in ISO format")

    @field_validator("from_date", "to_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate ISO date format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected ISO 8601 format (e.g., 2024-01-01)")

    def validate_range(self):
        """Validate that from_date is before to_date."""
        from_dt = datetime.fromisoformat(self.from_date.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(self.to_date.replace('Z', '+00:00'))
        if from_dt > to_dt:
            raise ValueError("'from' date must be before 'to' date")


class Filters(BaseModel):
    """Search filters."""
    date_range: Optional[DateRange] = None


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

    doc_id: str = Field(..., description="Document identifier")
    doc_name: str = Field(..., description="Document name")
    snippet: str = Field(..., description="Relevant text snippet")
    score: float = Field(..., description="Relevance score")


class SearchResponse(BaseModel):
    """Search response model matching the search service API."""

    results: List[SearchResult] = Field(default_factory=list, description="List of search results")
    query_expanded: str = Field(..., description="Query expanded with synonyms")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    request_id: str = Field(..., description="Unique request identifier")
    text: str = Field(..., description="Concatinated text from all docs")
