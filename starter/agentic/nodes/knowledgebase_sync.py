from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from starter.agentic.mcp_tool_utils import McpToolFilter


async def knowledgebase_sync_node(
    state: UdaHubState, config: RunnableConfig
) -> UdaHubState:
    tools = config.get("configurable", {}).get("mcp_tools", [])
    sync_tools = (
        McpToolFilter(tools)
        .by_author("UDAHub Knowledge Base")
        .by_tags(["sync"])
        .get_all()
    )
    print("Synchronizing knowledge base...")
    for tool in sync_tools:
        print(f"...{tool.name}()")
        await tool.ainvoke({})

    print("Knowledge base synchronized.\n")

    return state
