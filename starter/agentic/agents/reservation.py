from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState


async def reservation_agent_node(
    state: UdaHubState, config: RunnableConfig
) -> UdaHubState:
    print("Calling Reservation")
    return state
