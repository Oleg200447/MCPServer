"""MCP Search Server - Model Context Protocol integration for search services.

This package provides a FastMCP-based server that enables semantic search
capabilities through integration with OpenSearch-based search services.
"""

__version__ = "1.0.0"
__author__ = "MCP Search Server Team"
__description__ = "Model Context Protocol server for search service integration"

from .server import mcp, search_documents
from .config import settings

__all__ = ["mcp", "search_documents", "settings"]
