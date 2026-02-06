from langchain_core.runnables import RunnableConfig
from langchain.chat_models import BaseChatModel
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from starter.agentic.state import UdaHubState
from starter.data.udahub_db import create_ticket
from pydantic import BaseModel, Field
from textwrap import dedent


class ConversationSummary(BaseModel):
    summary: str = Field(
        description="A short summary of the conversation, suitable for the topic of a ticket in a ticketing system."
    )
    tags: list[str] = Field(
        description="A list of tags that are relevant for the conversation, e.g. 'billing', 'account', 'password', etc."
    )


async def summarize_conversation(
    messages: list[BaseMessage], llm: BaseChatModel
) -> ConversationSummary:
    conversation = "\n================================================\n".join(
        [f"{message.type}: {message.content}" for message in messages]
    )

    agent = create_agent(
        model=llm,
        system_prompt=dedent(f"""
        You are a helpful assistant for summarizing conversations between customers and support agents.
        You get the full conversation as input and your task is to create a short summary that captures the main topic of the conversation.
        The summary should be concise and should not contain any details that are not relevant to the main topic.
        The summary should be suitable for the topic of a ticket in a ticketing system, so it should be short and to the point.
        Do not use more than 150 characters for the summary.
        Additionally pick up to five relevant tags that describe the topic of the conversation.

        Conversation:
        {conversation}
        """),
        response_format=ConversationSummary,
    )

    response = await agent.ainvoke({}, config={"recursion_limit": 5})
    structured_response: ConversationSummary = response["structured_response"]

    return structured_response


async def memorization_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    ticket_id = config.get("configurable", {}).get("ticket_id")
    user = state.get("user", {})
    account_id = user.get("account_id", "")
    external_user_id = user.get("external_user_id", "")
    udahub_user_id = user.get("uda_hub_user_id", "")
    llm = config.get("configurable", {}).get("llm")
    loaded_messages_count = state.get("loaded_messages_count", 0)

    if not ticket_id:
        messages_to_store = state.get("messages", [])[loaded_messages_count:]
        summary = await summarize_conversation(messages_to_store, llm)  # ty:ignore[invalid-argument-type]

        ticket_id = create_ticket(
            account_id=account_id,
            user_id=udahub_user_id,
            channel="chat",
            summary=summary.summary,
            status="open",  # TODO: replace by value from state
            tags=summary.tags,
        )

    print(
        f"You can contine this conversation anytime by providing the ticket ID: {ticket_id}\n"
    )

    return state
