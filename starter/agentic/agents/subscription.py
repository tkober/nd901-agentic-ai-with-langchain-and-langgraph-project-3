from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState


async def subscription_agent_node(
    state: UdaHubState, config: RunnableConfig
) -> UdaHubState:
    print("Calling Subscription")
    return state
