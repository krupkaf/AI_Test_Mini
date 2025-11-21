"""Main Chainlit application entry point."""

import chainlit as cl
from langchain_core.messages import HumanMessage, AIMessage

from graph import graph
from state import ChatState


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    # Get current messages from session
    messages = cl.user_session.get("messages", [])

    # Add user message
    messages.append(HumanMessage(content=message.content))

    # Create initial state
    state: ChatState = {"messages": messages}

    # Create response message placeholder
    response_message = cl.Message(content="")
    await response_message.send()

    # Debug
    async with cl.Step(name="🔧 Debug Info") as step:
        result = await graph.ainvoke(state)
        ai_message = result["messages"][-1]

        usage = ai_message.response_metadata.get("token_usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        step.output = (
            f"Tokens: {prompt_tokens} prompt + {completion_tokens} completion"
        )

    # Update response
    response_message.content = ai_message.content
    await response_message.update()

    # Update session with new messages
    messages.append(AIMessage(content=ai_message.content))
    cl.user_session.set("messages", messages)
