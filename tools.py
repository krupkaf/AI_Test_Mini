"""MCP tool management for the AI agent.

This module provides MCP server integration via langchain-mcp-adapters.
MCP servers are configured in .env via MCP_SERVERS JSON.
"""

import logging
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from config import get_settings

logger = logging.getLogger(__name__)

# Global MCP client instance
_mcp_client: MultiServerMCPClient | None = None


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
