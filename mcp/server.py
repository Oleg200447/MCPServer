"""MCP Search Server - FastMCP-based server for search service integration.

This server provides a Model Context Protocol (MCP) interface for querying
a search service via HTTP. It uses Server-Sent Events (SSE) transport for
communication and includes comprehensive validation and error handling.
"""

import logging
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from config import settings
from models import logger
from clients.search_service_client import search_client
from tools import search_documents


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
