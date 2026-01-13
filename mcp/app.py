"""MCP application instance.

This module contains the FastMCP server instance.
"""

from fastmcp import FastMCP

# Create MCP server with SSE transport
mcp = FastMCP(
    "MCP Search Server"
)
