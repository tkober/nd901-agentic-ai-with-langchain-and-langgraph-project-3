from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from langchain.messages import AIMessage


def escalate_to_human_agent_node(
    state: UdaHubState, config: RunnableConfig
) -> UdaHubState:
    return {
        "messages": [AIMessage("I am forwarding you to a human agent...")],
        "terminate_chat": True,
    }
