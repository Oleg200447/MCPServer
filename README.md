# MCP Search Server

A Model Context Protocol (MCP) server built with FastMCP that provides semantic search capabilities by integrating with an OpenSearch-based search service. This server uses Server-Sent Events (SSE) transport and includes comprehensive validation, error handling, and Docker support.

## Features

- ✅ **FastMCP Integration**: Built on FastMCP framework with SSE transport
- ✅ **Pydantic Validation**: Comprehensive input/output validation
- ✅ **Docker Support**: Multi-stage Dockerfile and docker-compose configuration
- ✅ **Retry Logic**: Automatic retry with exponential backoff
- ✅ **Structured Logging**: JSON and console logging support
- ✅ **Health Checks**: Built-in health monitoring
- ✅ **Type Safety**: Full type hints throughout the codebase
- ✅ **Security**: Non-root user in Docker container
- ✅ **Configurable**: Environment-based configuration

## Architecture

```
┌─────────────────┐          ┌──────────────────┐          ┌─────────────────┐
│   MCP Client    │   SSE    │  MCP Search      │   HTTP   │ Search Service  │
│  (Claude/App)   │ ────────►│     Server       │ ────────►│  (OpenSearch)   │
└─────────────────┘          └──────────────────┘          └─────────────────┘
                                      │
                                      │
                                      ▼
                              ┌──────────────┐
                              │  Docker      │
                              │  Network     │
                              │ test_network │
                              └──────────────┘
```

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- Search service running on `search_service:8008` (or configured URL)

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   cd d:\projects\DeepResearch\MCPSearch
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp mcp/.env.example mcp/.env
   # Edit mcp/.env with your configuration
   ```

4. **Run the server**
   ```bash
   cd mcp
   python server.py
   ```

The server will start on `http://0.0.0.0:8080`

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d --build
   ```

2. **Check logs**
   ```bash
   docker logs -f mcp_search_server
   ```

3. **Check health**
   ```bash
   curl http://localhost:8080/health
   ```

## Configuration

All configuration is managed through environment variables. Edit `mcp/.env` or set environment variables directly.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCH_SERVICE_URL` | `http://search_service:8008` | Base URL of the search service |
| `SEARCH_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `MCP_SERVER_HOST` | `0.0.0.0` | Server bind address |
| `MCP_SERVER_PORT` | `8080` | Server port |
| `DEFAULT_USER_ID` | `system` | Default user ID for requests |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log format (json or console) |
| `MAX_RETRIES` | `3` | Maximum retry attempts for failed requests |
| `RETRY_DELAY` | `1.0` | Base delay between retries in seconds |

### Example .env File

```env
# Search Service Configuration
SEARCH_SERVICE_URL=http://search_service:8008
SEARCH_TIMEOUT=30

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080

# Default Values
DEFAULT_USER_ID=system

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Request Configuration
MAX_RETRIES=3
RETRY_DELAY=1.0
```

## Usage

### Available Tools

#### `search_documents`

Search for documents in OpenSearch indices using the integrated search service.

**Parameters:**

- `query` (string, required): Search query text (minimum 1 character)
- `user_id` (string, required): User identifier for tracking
- `indices` (array of strings, required): OpenSearch indices to search
- `filters` (object, optional): Search filters
  - `categories` (array of strings): Filter by categories
  - `date_from` (string): Start date (ISO format)
  - `date_to` (string): End date (ISO format)
  - `tags` (array of strings): Filter by tags
  - `metadata` (object): Additional metadata filters

**Returns:**

```json
{
  "results": [
    {
      "id": "doc_123",
      "score": 0.95,
      "index": "documents",
      "source": {
        "title": "Document Title",
        "content": "Document content..."
      },
      "highlights": {
        "content": ["...highlighted <em>text</em>..."]
      }
    }
  ],
  "query_expanded": "query with synonyms",
  "processing_time_ms": 45.2,
  "request_id": "req_abc123"
}
```

### Example Usage

**Basic Search:**

```python
{
  "query": "machine learning",
  "user_id": "user123",
  "indices": ["documents"]
}
```

**Advanced Search with Filters:**

```python
{
  "query": "deep learning",
  "user_id": "researcher_001",
  "indices": ["research_papers", "articles"],
  "filters": {
    "categories": ["AI", "Machine Learning"],
    "tags": ["neural-networks", "computer-vision"],
    "date_from": "2023-01-01",
    "date_to": "2024-12-31",
    "metadata": {
      "language": "en",
      "difficulty": "advanced"
    }
  }
}
```

## API Documentation

### Search Service Integration

The MCP server communicates with a search service at `http://search_service:8008/search` (configurable).

**Expected Search Service API:**

- **Endpoint**: `POST /search`
- **Content-Type**: `application/json`

**Request Body:**

```json
{
  "query": "search text",
  "user_id": "user_identifier",
  "indices": ["index1", "index2"],
  "filters": {
    "categories": ["category1"],
    "date_from": "2023-01-01",
    "date_to": "2024-12-31",
    "tags": ["tag1", "tag2"],
    "metadata": {}
  }
}
```

**Response Body:**

```json
{
  "results": [...],
  "query_expanded": "expanded query",
  "processing_time_ms": 45.2,
  "request_id": "unique_id"
}
```

## Docker

### Building the Image

```bash
docker build -t mcp-search-server .
```

### Running the Container

```bash
docker run -d \
  --name mcp_search_server \
  --network test_network \
  -p 8080:8080 \
  -e SEARCH_SERVICE_URL=http://search_service:8008 \
  mcp-search-server
```

### Docker Compose

The provided `docker-compose.yml` sets up:

- MCP Search Server on port 8080
- Connected to `test_network`
- Health checks enabled
- Automatic restart policy
- Logging configuration

**Start services:**

```bash
docker-compose up -d
```

**Stop services:**

```bash
docker-compose down
```

**View logs:**

```bash
docker-compose logs -f mcp_search_server
```

## Development

### Project Structure

```
MCPSearch/
├── mcp/
│   ├── __init__.py
│   ├── server.py           # Main MCP server implementation
│   ├── config.py           # Configuration management
│   ├── .env                # Environment variables
│   ├── prompts/
│   │   └── search_prompts.md  # Usage examples and documentation
│   └── tools/              # (Reserved for additional tools)
├── requirements.txt        # Python dependencies
├── Dockerfile             # Multi-stage Docker build
├── docker-compose.yml     # Docker orchestration
└── README.md             # This file
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (if implemented)
pytest tests/
```

### Code Quality

The codebase follows:

- **PEP 8** style guidelines
- **Type hints** throughout
- **Docstrings** for all public functions
- **Pydantic** for data validation
- **Structured logging** with context

### Adding New Tools

To add new MCP tools:

1. Define the tool function in `server.py` or create a new module in `mcp/tools/`
2. Decorate with `@mcp.tool()`
3. Add proper type hints and docstrings
4. Update documentation in `prompts/` directory

Example:

```python
@mcp.tool()
async def new_tool(param: str) -> Dict[str, Any]:
    """Tool description.
    
    Args:
        param: Parameter description
        
    Returns:
        Result description
    """
    # Implementation
    return {"result": "data"}
```

## Logging

The server uses structured logging with configurable output format.

**JSON Format** (default for production):

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "event": "search_request_successful",
  "request_id": "req_123",
  "results_count": 5,
  "processing_time_ms": 45.2
}
```

**Console Format** (for development):

```
2024-01-15 10:30:45 [info] search_request_successful request_id=req_123 results_count=5
```

Configure via `LOG_FORMAT` environment variable.

## Error Handling

The server implements comprehensive error handling:

### Validation Errors

```json
{
  "error": "Validation failed: query must be at least 1 character"
}
```

### HTTP Errors

```json
{
  "error": "Search service returned error 500: Internal Server Error"
}
```

### Connection Errors

```json
{
  "error": "Failed to connect to search service: Connection refused"
}
```

### Retry Logic

- Automatic retry for 5xx errors and connection failures
- Exponential backoff: 1s, 2s, 3s
- Maximum 3 retry attempts (configurable)

## Troubleshooting

### Server Won't Start

1. Check if port 8080 is available:
   ```bash
   netstat -ano | findstr :8080  # Windows
   lsof -i :8080                 # Linux/Mac
   ```

2. Verify Python version:
   ```bash
   python --version  # Should be 3.11+
   ```

3. Check configuration:
   ```bash
   cat mcp/.env
   ```

### Can't Connect to Search Service

1. Verify search service is running:
   ```bash
   docker ps | grep search_service
   ```

2. Check network connectivity:
   ```bash
   docker network inspect test_network
   ```

3. Test search service directly:
   ```bash
   curl -X POST http://search_service:8008/search \
     -H "Content-Type: application/json" \
     -d '{"query":"test","user_id":"test","indices":["test"]}'
   ```

### Container Issues

1. Check container logs:
   ```bash
   docker logs mcp_search_server
   ```

2. Inspect container:
   ```bash
   docker inspect mcp_search_server
   ```

3. Rebuild image:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Performance

### Optimization Tips

1. **Connection Pooling**: HTTP client uses connection pooling (max 20 connections)
2. **Timeout Configuration**: Adjust `SEARCH_TIMEOUT` based on search complexity
3. **Retry Strategy**: Configure `MAX_RETRIES` and `RETRY_DELAY` for your needs
4. **Index Selection**: Only search necessary indices to improve performance
5. **Filter Usage**: Use filters instead of including criteria in query text

### Monitoring

Key metrics to monitor:

- `processing_time_ms` in search responses
- HTTP request/response times
- Error rates and retry attempts
- Container resource usage

## Security

### Best Practices Implemented

- ✅ Non-root user in Docker container (UID 1000)
- ✅ No sensitive data in logs
- ✅ Input validation with Pydantic
- ✅ Timeout protection against slow requests
- ✅ Health check endpoints
- ✅ Minimal container image (python:3.11-slim)

### Recommendations

1. Use HTTPS in production
2. Implement authentication/authorization
3. Set up rate limiting
4. Use secrets management for sensitive config
5. Regular security updates for dependencies

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Update documentation
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues and questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker logs mcp_search_server`
3. Check search service logs
4. Open an issue on GitHub

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenSearch Documentation](https://opensearch.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

## Changelog

### Version 1.0.0 (2024-01-15)

- Initial release
- FastMCP integration with SSE transport
- Search documents tool
- Pydantic validation
- Docker support
- Comprehensive documentation

---

**Built with ❤️ using FastMCP and Python**
