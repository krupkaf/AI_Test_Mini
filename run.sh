#!/bin/bash
set -e

# Sync dependencies
echo "Syncing dependencies..."
uv sync

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Start Chainlit (MCP servers are started automatically via langchain-mcp-adapters)
echo "Starting ABRA Gen AI Assistant..."
uv run chainlit run app.py -w --host 0.0.0.0 --port 8000
