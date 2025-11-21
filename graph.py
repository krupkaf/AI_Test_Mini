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


if __name__ == "__main__":
    """Generate mermaid diagram and update README.md."""
    import re

    mermaid_code = graph.get_graph().draw_mermaid()
    diagram = f"```mermaid\n{mermaid_code}\n```"

    with open("README.md", "r") as f:
        readme = f.read()

    pattern = r"(<!-- GRAPH:START -->).*?(<!-- GRAPH:END -->)"
    replacement = rf"\1\n{diagram}\n\2"
    readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open("README.md", "w") as f:
        f.write(readme)

    print("Graph diagram updated in README.md")
