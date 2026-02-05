from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from langchain_core.messages import AIMessage
from starter.agentic.mcp_tool_utils import McpToolFilter


async def browsing_agent_node(
    state: UdaHubState, config: RunnableConfig
) -> UdaHubState:
    tools = config.get("configurable", {}).get("mcp_tools", [])
    llm = config.get("configurable", {}).get("llm")
    user = state.get("user", {})
    account_id = user.get("account_id", "")

    print("Available tools:")
    print(McpToolFilter(tools).by_tags(["browsing", account_id]))

    return {
        "messages": [AIMessage(content="Browsing Agent activated")],
        "has_pending_messages": True,
        "terminate_chat": True,
    }
