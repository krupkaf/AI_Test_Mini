"""Main Chainlit application entry point."""

import logging

import bcrypt
import chainlit as cl
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from config import get_settings
from graph import create_graph
from state import AgentState
from tools import get_tools

logger = logging.getLogger(__name__)


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    """Authenticate user against AUTH_USERS from .env."""
    users = get_settings().get_auth_users()
    logger.info(f"Auth attempt for user: {username}, configured users: {list(users.keys())}")

    if not users:
        logger.info("No users configured - allowing anonymous access")
        return cl.User(identifier="anonymous", metadata={"role": "user"})

    if username not in users:
        logger.warning(f"User {username} not found")
        return None

    stored_hash = users[username]
    try:
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            logger.info(f"User {username} authenticated successfully")
            return cl.User(identifier=username, metadata={"role": "user"})
    except Exception as e:
        logger.error(f"Password check failed: {e}")

    logger.warning(f"Invalid password for user {username}")
    return None


def extract_tool_calls(messages: list) -> list[dict]:
    """Extract tool calls from message history."""
    tool_calls = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "name": tc["name"],
                    "args": tc["args"],
                })
    return tool_calls


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with MCP tools."""
    # Load tools from MCP servers
    tools = await get_tools()

    # Create graph with tools
    graph = create_graph(tools)

    # Store in session
    cl.user_session.set("graph", graph)
    cl.user_session.set("messages", [])
    cl.user_session.set("tool_count", len(tools))

    if tools:
        tool_names = [t.name for t in tools]
        await cl.Message(content=f"Loaded {len(tools)} tools: {', '.join(tool_names)}").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    # Get graph and messages from session
    graph = cl.user_session.get("graph")
    messages = cl.user_session.get("messages", [])

    if graph is None:
        await cl.Message(content="Session not initialized. Please refresh.").send()
        return

    # Add user message
    messages.append(HumanMessage(content=message.content))

    # Create initial state
    state: AgentState = {"messages": messages}

    # Create response message placeholder
    response_message = cl.Message(content="")
    await response_message.send()

    # Debug
    async with cl.Step(name="🔧 Debug Info") as step:
        result = await graph.ainvoke(state)
        ai_message = result["messages"][-1]

        # Extract tool calls from result
        tool_calls = extract_tool_calls(result["messages"])

        # Build debug output
        debug_lines = []

        if tool_calls:
            debug_lines.append("**Tool calls:**")
            for tc in tool_calls:
                debug_lines.append(f"- `{tc['name']}({tc['args']})`")
            debug_lines.append("")

        usage = ai_message.response_metadata.get("token_usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        debug_lines.append(f"**Tokens:** {prompt_tokens} prompt + {completion_tokens} completion")

        step.output = "\n".join(debug_lines)

    # Update response
    response_message.content = ai_message.content
    await response_message.update()

    # Update session with new messages
    messages.append(AIMessage(content=ai_message.content))
    cl.user_session.set("messages", messages)
