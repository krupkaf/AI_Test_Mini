"""Configuration loading for the chatbot."""

import json
from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openrouter_api_key: str
    model_name: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7

    # MCP servers configuration as JSON string
    # Format: {"server_name": {"command": "...", "args": [...], "transport": "stdio"}}
    mcp_servers: str = "{}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_mcp_config(self) -> dict[str, Any]:
        """Parse MCP servers configuration from JSON string."""
        try:
            return json.loads(self.mcp_servers)
        except json.JSONDecodeError:
            return {}


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
