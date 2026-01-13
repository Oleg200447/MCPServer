"""Configuration management for MCP Search Server.

This module handles loading and validating environment variables
and application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Search service configuration
    search_service_url: str = "http://search_service:8008"
    search_timeout: int = 30
    
    # MCP server configuration
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8080
    
    # Default values
    default_user_id: str = "system"
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Request configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def get_search_endpoint(self) -> str:
        """Get the full search endpoint URL."""
        return f"{self.search_service_url}/search"


# Global settings instance
settings = Settings()
