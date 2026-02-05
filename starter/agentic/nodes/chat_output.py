from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from langchain.messages import AIMessage


def chat_output_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    messages = state.get("messages", [])
    last_printed_idx = state.get("last_printed_idx", -1)
    chat_interface = config.get("configurable", {}).get("chat_interface")

    if not chat_interface:
        raise Exception("No chat interface found")

    ai_messages: list[AIMessage] = [m for m in messages if isinstance(m, AIMessage)]
    for i in range(last_printed_idx + 1, len(ai_messages)):
        chat_interface.read_message(str(ai_messages[i].content))

    return {"messages": [], "last_printed_idx": len(ai_messages) - 1}
