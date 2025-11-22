"""MCP tool management for the AI agent.

This module provides MCP server integration via langchain-mcp-adapters.
MCP servers are configured in .env via MCP_SERVERS JSON.
"""

import logging
import os
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from config import get_settings

logger = logging.getLogger(__name__)

# Global MCP client instance
_mcp_client: MultiServerMCPClient | None = None


def _inject_env_vars(mcp_config: dict[str, Any]) -> dict[str, Any]:
    """Inject ABRA_* environment variables into MCP server configs.

    This ensures MCP subprocesses receive the necessary environment variables.
    """
    abra_vars = {k: v for k, v in os.environ.items() if k.startswith("ABRA_")}

    if not abra_vars:
        return mcp_config

    for server_name, server_config in mcp_config.items():
        if "env" not in server_config:
            server_config["env"] = {}
        # Add ABRA vars without overwriting existing
        for key, value in abra_vars.items():
            if key not in server_config["env"]:
                server_config["env"][key] = value

    return mcp_config


def get_mcp_client() -> MultiServerMCPClient | None:
    """Get or create MCP client from configuration.

    Returns:
        MultiServerMCPClient if MCP servers are configured, None otherwise.
    """
    global _mcp_client

    if _mcp_client is not None:
        return _mcp_client

    settings = get_settings()
    mcp_config = settings.get_mcp_config()

    if not mcp_config:
        logger.info("No MCP servers configured")
        return None

    # Inject environment variables for MCP subprocesses
    mcp_config = _inject_env_vars(mcp_config)

    logger.info(f"Initializing MCP client with servers: {list(mcp_config.keys())}")
    _mcp_client = MultiServerMCPClient(mcp_config)
    return _mcp_client


async def get_tools() -> list:
    """Get all tools from configured MCP servers.

    Returns:
        List of LangChain tools from MCP servers.
    """
    client = get_mcp_client()

    if client is None:
        return []

    try:
        tools = await client.get_tools()
        logger.info(f"Loaded {len(tools)} tools from MCP servers")
        return tools
    except Exception as e:
        logger.error(f"Failed to load MCP tools: {e}")
        return []


async def cleanup_mcp_client() -> None:
    """Cleanup MCP client connections."""
    global _mcp_client

    if _mcp_client is not None:
        try:
            await _mcp_client.__aexit__(None, None, None)
        except Exception as e:
            logger.error(f"Error closing MCP client: {e}")
        _mcp_client = None
