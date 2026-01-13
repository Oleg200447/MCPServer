"""MCP Search Server - FastMCP-based server for search service integration.

This server provides a Model Context Protocol (MCP) interface for querying
a search service via HTTP. It uses Server-Sent Events (SSE) transport for
communication and includes comprehensive validation and error handling.
"""

import asyncio
import logging
import structlog
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

import httpx
from fastmcp import FastMCP
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


# ============================================================================
# Pydantic Models for Validation
# ============================================================================

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


# ============================================================================
# HTTP Client Management
# ============================================================================

class SearchServiceClient:
    """HTTP client for communicating with the search service."""
    
    def __init__(self):
        """Initialize the HTTP client."""
        self.client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()
        
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client instance."""
        async with self._client_lock:
            if self.client is None or self.client.is_closed:
                self.client = httpx.AsyncClient(
                    timeout=httpx.Timeout(settings.search_timeout),
                    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
                )
            return self.client
    
    async def close(self):
        """Close the HTTP client."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute a search request against the search service.
        
        Args:
            request: Validated search request
            
        Returns:
            SearchResponse containing search results
            
        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response cannot be parsed
        """
        client = await self.get_client()
        endpoint = settings.get_search_endpoint()
        
        logger.info(
            "executing_search_request",
            endpoint=endpoint,
            query=request.query,
            user_id=request.user_id,
            indices=request.indices
        )
        
        # Retry logic
        last_exception = None
        for attempt in range(settings.max_retries):
            try:
                response = await client.post(
                    endpoint,
                    json=request.model_dump(exclude_none=True),
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                # Parse and validate response
                result = SearchResponse(**response.json())
                
                logger.info(
                    "search_request_successful",
                    request_id=result.request_id,
                    results_count=len(result.results),
                    processing_time_ms=result.processing_time_ms
                )
                
                return result
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.error(
                    "search_request_failed",
                    status_code=e.response.status_code,
                    response_body=e.response.text,
                    attempt=attempt + 1
                )
                
                if e.response.status_code >= 500 and attempt < settings.max_retries - 1:
                    await asyncio.sleep(settings.retry_delay * (attempt + 1))
                    continue
                raise
                
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                logger.error(
                    "search_request_error",
                    error=str(e),
                    attempt=attempt + 1
                )
                
                if attempt < settings.max_retries - 1:
                    await asyncio.sleep(settings.retry_delay * (attempt + 1))
                    continue
                raise
        
        # If we exhausted retries, raise the last exception
        if last_exception:
            raise last_exception
        raise RuntimeError("Search request failed after all retries")


# Global client instance
search_client = SearchServiceClient()


# ============================================================================
# FastMCP Server Setup
# ============================================================================

# Create MCP server with SSE transport
mcp = FastMCP(
    "MCP Search Server",
    dependencies=[]
)


@asynccontextmanager
async def lifespan_manager(app):
    """Manage application lifespan - startup and shutdown."""
    logger.info(
        "mcp_server_starting",
        search_service_url=settings.search_service_url,
        mcp_server_host=settings.mcp_server_host,
        mcp_server_port=settings.mcp_server_port
    )
    yield
    logger.info("mcp_server_shutting_down")
    await search_client.close()


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
async def search_documents(
    query: str,
    user_id: str,
    indices: List[str],
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Search for documents in OpenSearch indices using the search service.
    
    This tool performs semantic search across specified OpenSearch indices,
    with optional filtering capabilities. The search service handles query
    expansion, relevance scoring, and result ranking.
    
    Args:
        query: The search query text (minimum 1 character)
        user_id: User identifier for tracking and personalization
        indices: List of OpenSearch index names to search (minimum 1 required)
        filters: Optional filters to narrow search results:
            - categories: List of category names
            - date_from: Start date for filtering (ISO format)
            - date_to: End date for filtering (ISO format)
            - tags: List of tags
            - metadata: Additional key-value metadata filters
    
    Returns:
        Dictionary containing:
            - results: List of search results with scores and highlights
            - query_expanded: Original query expanded with synonyms
            - processing_time_ms: Processing time in milliseconds
            - request_id: Unique identifier for this search request
    
    Raises:
        ValueError: If validation fails (empty query, no indices, etc.)
        HTTPError: If the search service is unavailable or returns an error
    
    Example:
        search_documents(
            query="machine learning algorithms",
            user_id="user123",
            indices=["documents", "papers"],
            filters={"categories": ["AI", "ML"], "tags": ["tutorial"]}
        )
    """
    try:
        # Parse filters if provided
        filters_obj = None
        if filters:
            filters_obj = Filters(**filters)
        
        # Create and validate search request
        search_request = SearchRequest(
            query=query,
            user_id=user_id,
            indices=indices,
            filters=filters_obj
        )
        
        logger.info(
            "tool_invoked",
            tool="search_documents",
            query=query,
            user_id=user_id,
            indices_count=len(indices)
        )
        
        # Execute search
        response = await search_client.search(search_request)
        
        # Convert to dictionary for MCP response
        return response.model_dump()
        
    except ValueError as e:
        logger.error("validation_error", error=str(e))
        raise ValueError(f"Validation failed: {str(e)}")
    
    except httpx.HTTPStatusError as e:
        logger.error(
            "http_error",
            status_code=e.response.status_code,
            response=e.response.text
        )
        raise RuntimeError(
            f"Search service returned error {e.response.status_code}: {e.response.text}"
        )
    
    except httpx.RequestError as e:
        logger.error("request_error", error=str(e))
        raise RuntimeError(f"Failed to connect to search service: {str(e)}")
    
    except Exception as e:
        logger.error("unexpected_error", error=str(e), error_type=type(e).__name__)
        raise RuntimeError(f"Unexpected error during search: {str(e)}")


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Run the MCP server with SSE transport."""
    import uvicorn
    
    # Configure logging level
    log_level = settings.log_level.lower()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
    
    logger.info(
        "starting_mcp_server",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        transport="sse"
    )
    
    # Run the server with SSE support
    uvicorn.run(
        mcp.sse_transport_asgi_app(),
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        log_level=log_level
    )


if __name__ == "__main__":
    main()
