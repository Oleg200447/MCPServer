"""Search tool for MCP Search Server.

This module contains the search_documents MCP tool.
"""

import httpx
from typing import List, Optional, Dict, Any

from server import mcp

from config import settings
from models import SearchRequest, Filters, logger
from clients.search_service_client import search_client


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
