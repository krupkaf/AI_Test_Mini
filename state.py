"""State definitions for the AI agent conversation."""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the AI agent conversation.

    Attributes:
        messages: List of conversation messages with automatic aggregation.
    """
    messages: Annotated[list, add_messages]
