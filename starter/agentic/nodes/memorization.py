from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState


async def memorization_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    return state
