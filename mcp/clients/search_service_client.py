"""Search service HTTP client.

This module provides an HTTP client for communicating with the search service.
"""

import asyncio
import httpx
from typing import Optional

from config import settings
from models import SearchRequest,SearchResult, SearchResponse, logger


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

                raw_data = response.json()

                # Собираем поле text для LLM
                if raw_data.get("results"):
                    full_text = "\n\n".join(
                        f"Document: {r['doc_name']} (ID: {r['doc_id']})\n{r['text']}"
                        for r in raw_data["results"]
                    )
                else:
                    full_text = "No results found"

                # Создаём объект SearchResponse с полем text
                result = SearchResponse(
                    results=[SearchResult(**r) for r in raw_data.get("results", [])],
                    query_expanded=raw_data.get("query_expanded", ""),
                    processing_time_ms=raw_data.get("processing_time_ms", 0.0),
                    request_id=raw_data.get("request_id", ""),
                    text=full_text
                )

                logger.info(
                    "search_request_successful",
                    request_id=result.request_id,
                    results_count=len(result.results),
                    processing_time_ms=result.processing_time_ms,
                    text = full_text
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
