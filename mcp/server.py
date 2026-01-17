"""MCP Search Server - FastMCP-based server for search service integration.

This server provides a Model Context Protocol (MCP) interface for querying
a search service via HTTP. It uses Server-Sent Events (SSE) transport for
communication and includes comprehensive validation and error handling.
"""

from app import mcp
from tools.search import setup_tools
from promts.search_promts import setup_promts

def main():
    """Run the MCP server."""

    setup_tools(mcp)
    setup_promts(mcp)

    mcp.run(
        host="0.0.0.0",    # слушать все интерфейсы внутри контейнера
        port=8080,         # совпадает с EXPOSE в Dockerfile
        transport="http"   # или "sse"
    )   


if __name__ == "__main__":
    main()
