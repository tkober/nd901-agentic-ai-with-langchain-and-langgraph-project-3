from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState


async def faq_agent_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    print("Calling FAQ")
    return state
