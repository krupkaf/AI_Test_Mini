"""State definitions for the chatbot conversation."""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    """State for the chatbot conversation.

    Attributes:
        messages: List of conversation messages with automatic aggregation.
    """
    messages: Annotated[list, add_messages]
