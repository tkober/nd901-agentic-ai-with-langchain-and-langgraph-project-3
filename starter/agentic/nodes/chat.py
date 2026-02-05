from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from langchain.messages import AIMessage, HumanMessage


def chat_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    messages = state.get("messages", [])
    last_printed_idx = state.get("last_printed_idx", -1)
    chat_interface = config.get("configurable", {}).get("chat_interface")

    if not chat_interface:
        raise Exception("No chat interface found")

    # Send pending messages
    ai_messages: list[AIMessage] = [m for m in messages if isinstance(m, AIMessage)]
    for i in range(last_printed_idx + 1, len(ai_messages)):
        chat_interface.read_message(str(ai_messages[i].content))

    # Read user input if necessary
    terminate_chat = state.get("terminate_chat", False)
    user_input = []
    if state.get("need_user_input", False):
        message = chat_interface.next_message()
        if not message:
            terminate_chat = True
        else:
            user_input.append(HumanMessage(message))

    return {
        "messages": user_input,
        "last_printed_idx": len(ai_messages) - 1,
        "has_pending_messages": False,
        "need_user_input": False,
        "terminate_chat": terminate_chat,
    }
