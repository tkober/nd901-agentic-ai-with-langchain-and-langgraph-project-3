from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from starter.agentic.state import UdaHubState
from starter.data.udahub_db import get_messages_for_ticket


async def enrichment_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    if state.get("is_enriched", False) is True:
        return state

    ticket_id = config.get("configurable", {}).get("ticket_id", None)
    messages = []
    loaded_messages_count = 0
    last_printed_idx = -1
    if ticket_id:
        loaded_messages = get_messages_for_ticket(ticket_id)

        ai_messages_count = 0
        for message in loaded_messages:
            if message.get("role") == "ai" and message.get("content"):
                messages.append(AIMessage(content=message.get("content")))
                ai_messages_count += 1

            if message.get("role") == "user" and message.get("content"):
                messages.append(HumanMessage(content=f"> {message.get('content')}"))

        print(
            f"\nLoaded {len(messages)} messages from long-term memory for ticket_id {ticket_id}\n"
        )
        loaded_messages_count = len(messages)

        # Print loaded messages
        chat_interface = config.get("configurable", {}).get("chat_interface")

        if not chat_interface:
            raise Exception("No chat interface found")

        for message in messages:
            chat_interface.read_message(str(message.content))

        last_printed_idx = len(messages) - 1

    else:
        user = state.get("user", {})
        account_id = user.get("account_id", "")
        account_name = user.get("account_name", account_id)
        full_name = user.get("full_name")
        udahub_user_id = user.get("udahub_user_id")

        # Greet the user
        if full_name:
            messages.append(
                AIMessage(
                    f"Welcome {full_name}!\n"
                    f"I am UDA-Hub and I will be helping you on behalf of {account_name}."
                )
            )

        # If this is the first interaction on behalf of the requested account let the user know.
        if user.get("udahub_user_created", False) is True:
            messages.append(
                AIMessage(
                    "It seems like I am serving you the first time. I created a new UDA Hub user for you to keep context.\n"
                    f"Your user ID with me is {udahub_user_id}\n"
                )
            )

    return {
        "messages": messages,
        "is_enriched": True,
        "loaded_messages_count": loaded_messages_count,
        "last_printed_idx": last_printed_idx,
    }
