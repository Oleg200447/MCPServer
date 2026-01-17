"""Search tool for MCP Search Server.

This module contains the search_documents MCP tool.
"""

import httpx
from typing import List, Optional, Dict, Any

# from app import mcp
from fastmcp import FastMCP

from models import SearchRequest, SearchResponse, Filters, logger
from clients.search_service_client import search_client

def setup_tools(server:FastMCP):
    @server.tool()
    async def search_documents(
        query: str,
        user_id: str,
        indices: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Search for documents in OpenSearch indices using the search service.

        This tool performs semantic search across specified OpenSearch indices,
        with optional filtering capabilities. The search service handles query
        expansion, relevance scoring, and result ranking. Search service was train for reranking with next quiries: 
        1. A short keyword-style query (1–3 words)
        2. A natural long phrase query (4–7 words)
        3. A question-style query (wh- format, e.g., "What...", "How...", "Why...")
        4. Another diverse keyword-style query
        5. Another natural phrase query, so this type off quiries has best perfomance.

        Args:
            query: The search query text
            user_id: User identifier for tracking and personalization
            indices: List of OpenSearch index names to search (minimum 1 required)
            filters: Optional filters to narrow search results:
                - date_range: Date range filter with 'from' and 'to' fields in ISO format

        Returns:
            Dictionary containing:
                - text: concatinate documents in one text


        Raises:
            ValueError: If validation fails (empty query, no indices, etc.)
            HTTPError: If the search service is unavailable or returns an error

        Example:
            search_documents(
                query="machine learning algorithms",
                user_id="user123",
                indices=["documents", "papers"],
                filters={"date_range": {"from": "2024-01-01", "to": "2024-12-31"}}
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

            response = await search_client.search(search_request)
            
            res_dict = response.model_dump()

            logger.info(
                "AHAHHAHA",
                **res_dict
            )


            return res_dict.get("text", "No documents found.")

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
