from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from langchain.messages import HumanMessage


def read_message_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    chat_interface = config.get("configurable", {}).get("chat_interface")
    terminate_chat = state.get("terminate_chat", False)

    if not chat_interface:
        raise Exception("No chat interface found")

    user_input = []
    message = chat_interface.next_message()
    if not message:
        terminate_chat = True
    else:
        user_input.append(HumanMessage(message))

    return {
        "messages": user_input,
        "need_user_input": False,
        "terminate_chat": terminate_chat,
    }
