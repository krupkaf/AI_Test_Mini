"""MCP server for Abra Gen API integration."""

import asyncio
import logging
import sys
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .client import AbraClient
from .config import get_config
from .tools import register_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


async def run_server() -> None:
    """Run the MCP server with Abra Gen API tools."""
    logger.info("Starting Abra MCP Server...")

    # Load and validate configuration
    try:
        config = get_config()
        logger.info(f"Configuration loaded: {config}")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize Abra API client
    client = AbraClient(config)

    # Create MCP server
    server = Server("abra-mcp-server")

    # Register tools
    register_tools(server, client)
    logger.info("Tools registered successfully")

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server started, waiting for requests...")
        try:
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
        finally:
            # Cleanup
            await client.close()
            logger.info("Server stopped")


def main() -> None:
    """Main entry point for the server."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
