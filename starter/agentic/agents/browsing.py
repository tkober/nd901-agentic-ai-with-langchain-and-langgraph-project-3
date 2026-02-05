from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from langchain_core.messages import AIMessage


async def browsing_agent_node(
    state: UdaHubState, config: RunnableConfig
) -> UdaHubState:
    return {
        "messages": [AIMessage(content="Browsing Agent activated")],
        "has_pending_messages": True,
        "terminate_chat": True,
    }
