from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState


async def supervisor_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    print("Calling superevisor")
    return state
