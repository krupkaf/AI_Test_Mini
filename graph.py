"""LangGraph AI agent with tool support."""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

from state import AgentState
from config import get_settings


def should_continue(state: AgentState) -> str:
    """Determine if the agent should continue to tools or end."""
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def create_graph(tools: list | None = None):
    """Create and compile the AI agent graph.

    Args:
        tools: List of tools available to the agent. If None, no tools are bound.
    """
    settings = get_settings()
    tools = tools or []

    # Configure LLM for OpenRouter
    llm = ChatOpenAI(
        model=settings.model_name,
        temperature=settings.temperature,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )

    # Bind tools to LLM if available
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    async def agent_node(state: AgentState) -> AgentState:
        """Process messages and decide on tool calls or response."""
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    # Build the graph
    graph_builder = StateGraph(AgentState)

    # Add nodes
    graph_builder.add_node("agent", agent_node)
    if tools:
        graph_builder.add_node("tools", ToolNode(tools))

    # Add edges
    graph_builder.add_edge(START, "agent")

    if tools:
        graph_builder.add_conditional_edges("agent", should_continue, ["tools", END])
        graph_builder.add_edge("tools", "agent")
    else:
        graph_builder.add_edge("agent", END)

    return graph_builder.compile()


if __name__ == "__main__":
    """Generate mermaid diagram and update README.md."""
    import re
    from langchain_core.tools import tool

    # Create a dummy tool to show the full architecture in diagram
    @tool
    def dummy_tool() -> str:
        """Placeholder tool for diagram generation."""
        return ""

    # Create graph with dummy tool to show agent-tools loop
    graph_with_tools = create_graph([dummy_tool])

    mermaid_code = graph_with_tools.get_graph().draw_mermaid()
    diagram = f"```mermaid\n{mermaid_code}\n```"

    with open("README.md", "r") as f:
        readme = f.read()

    pattern = r"(<!-- GRAPH:START -->).*?(<!-- GRAPH:END -->)"
    replacement = rf"\1\n{diagram}\n\2"
    readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open("README.md", "w") as f:
        f.write(readme)

    print("Graph diagram updated in README.md")
