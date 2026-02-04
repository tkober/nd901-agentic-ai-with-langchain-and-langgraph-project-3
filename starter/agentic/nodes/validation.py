from langchain_core.runnables import RunnableConfig
from langchain.messages import AIMessage
from starter.agentic.state import UdaHubState, TaskContext
from starter.agentic.mcp_tool_utils import McpToolFilter
from starter.agentic.agents.user_validation import user_validation_agent


async def validation_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    # Check if is already validated
    if state.get("is_validated", False) is True:
        return state

    tools = config.get("configurable", {}).get("mcp_tools", [])
    llm = config.get("configurable", {}).get("llm")
    user = state.get("user", {})
    account_id = user.get("account_id", "")
    external_user_id = user.get("external_user_id", "")

    # Check that the provided account id belongs to a customer of UDA Hub
    account_lookup_tool = McpToolFilter(tools).by_name("get_udahub_account").get_first()
    response = await account_lookup_tool.ainvoke(
        {"account": {"account_id": account_id}}
    )
    if len(response) == 0:
        return {
            "messages": [AIMessage(content="The provided account ID is invalid.")],
            "task": TaskContext(status="failed", error="Invalid account ID"),
        }

    # Validate the provided user
    validation_tools = []
    validation_tools.extend(
        McpToolFilter(tools).by_author("UDAHub").by_tags(["validation"]).get_all()
    )
    validation_tools.extend(
        McpToolFilter(tools)
        .by_author(account_id)
        .by_read_only(True)
        .by_tags(["validation"])
        .get_all()
    )
    response = await user_validation_agent(
        llm=llm,
        tools=validation_tools,
        account_id=account_id,
        external_user_id=external_user_id,
    )

    # In case validation failed let the user know
    if not response.validation_successfull:
        return {
            "messages": [
                AIMessage(
                    content=f"I was unable to validate your identity. If this issue persists please reach out to '{account_id}'."
                )
            ],
            "task": TaskContext(status="failed", error=f"{response.error_message}"),
        }

    # Greet the user
    messages = []
    if response.full_name:
        messages.append(
            AIMessage(
                f"Welcome {response.full_name}!\n"
                f"I am UDA Hub and I will be helping you on behalf of {response.account_id}."
            )
        )

    # If this is the first interaction on behalf of the requested account let the user know.
    if response.uda_hub_user_created:
        messages.append(
            AIMessage(
                "It seems like I am serving you the first time. I created a new UDA Hub user for you to keep context."
                f"Your user ID with me is {response.uda_hub_user_id}"
            )
        )

    return {
        "messages": messages,
        "is_validated": True,
        "user": {
            "account_id": account_id,
            "external_user_id": external_user_id,
            "udahub_user_id": f"{response.uda_hub_user_id}",
            "full_name": f"{response.full_name}",
        },
    }
