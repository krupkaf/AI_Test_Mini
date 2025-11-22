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

    # User authentication as JSON string
    # Format: {"username": "bcrypt_hash", ...}
    auth_users: str = "{}"

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

    def get_auth_users(self) -> dict[str, str]:
        """Parse user authentication from JSON string.

        Supports both plain bcrypt hashes and base64-encoded hashes.
        Use base64 encoding to avoid $ interpretation in Docker env files.

        Returns:
            Dict mapping username to bcrypt password hash.
        """
        import base64

        try:
            users = json.loads(self.auth_users)
        except json.JSONDecodeError:
            return {}

        # Decode base64 hashes if needed (base64 hashes don't start with $)
        decoded = {}
        for username, hash_value in users.items():
            if hash_value.startswith("$"):
                # Plain bcrypt hash
                decoded[username] = hash_value
            else:
                # Base64 encoded hash
                try:
                    decoded[username] = base64.b64decode(hash_value).decode("utf-8")
                except Exception:
                    decoded[username] = hash_value
        return decoded


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
