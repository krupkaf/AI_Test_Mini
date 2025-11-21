"""LangGraph conversation graph definition."""

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

from state import ChatState
from config import get_settings


def create_graph():
    """Create and compile the conversation graph."""
    settings = get_settings()

    # Configure ChatOpenAI for OpenRouter
    llm = ChatOpenAI(
        model=settings.model_name,
        temperature=settings.temperature,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )

    async def chatbot_node(state: ChatState) -> ChatState:
        """Process user message and generate response."""
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    # Build the graph
    graph_builder = StateGraph(ChatState)
    graph_builder.add_node("chatbot", chatbot_node)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    return graph_builder.compile()


# Singleton graph instance
graph = create_graph()
