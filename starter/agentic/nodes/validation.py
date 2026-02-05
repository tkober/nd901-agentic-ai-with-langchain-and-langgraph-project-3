from typing import Optional
from pydantic import BaseModel, Field
from langchain.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langchain.messages import AIMessage, SystemMessage
from langgraph.errors import GraphRecursionError
from starter.agentic.state import UdaHubState, TaskContext
from starter.agentic.mcp_tool_utils import McpToolFilter
from starter.data.udahub_db import get_account_by_id


class UserValidationResult(BaseModel):
    account_id: str = Field(description="The account ID of the UDA Hub customer")
    uda_hub_user_id: Optional[str] = Field(
        None, description="The users ID in UDA Hubs system"
    )
    full_name: Optional[str] = Field(
        None, description="The name of the user if validation was successful."
    )
    external_user_id: str = Field(description="The users ID in the customers system")
    uda_hub_user_created: bool = Field(
        description="A flag that shows whether a new UDA Hub user had to be created",
        default=False,
    )
    validation_successfull: bool = Field(
        description="A flag that shows whether the user could be validated with the customer",
        default=False,
    )
    error_message: Optional[str] = Field(
        None, description="The error message in case the validation failed"
    )


async def validate_user(
    llm: BaseChatModel, tools: list, account_id: str, external_user_id: str
) -> UserValidationResult:
    agent = create_agent(
        model=llm,
        system_prompt=SystemMessage(f"""
        You are a validation agent for UDA Hub. You need to validate a user for the customer with the account_id='{account_id}'.
        It has already been checked, that {account_id} is a legit customer of UDA Hub. 
        You have tools for accessing both UDA Hubs system and the system of the customer. 

        The user with the external user with user_id='{external_user_id}' needs to be validated using the following steps:

        Check with the customer whether with user exists. If you cannot find a user in the customers system it is an invalid user and you terminate here.
        If you find a user check with UDA Hub whether there is a user. If you find one terminate here. If not create a new one.

        Rules:
        - Do call tools only ones
        - Do not try to create a new user on UDA Hub if you already found one
        """),
        tools=tools,
        response_format=UserValidationResult,
    )

    try:
        result = await agent.ainvoke({}, config={"recursion_limit": 10})
        return result["structured_response"]

    except GraphRecursionError:
        return UserValidationResult(
            account_id=account_id,
            external_user_id=external_user_id,
            uda_hub_user_created=False,
            validation_successfull=False,
            error_message="An internal error occurred.",
        ).model_dump()


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
    account = get_account_by_id(account_id)
    if account is None:
        return {
            "messages": [AIMessage(content="The provided account ID is invalid.")],
            "task": TaskContext(status="failed", error="Invalid account ID"),
            "terminate_chat": True,
            "has_pending_messages": True,
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
    response = await validate_user(
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
            "terminate_chat": True,
            "has_pending_messages": True,
            "task": TaskContext(status="failed", error=f"{response.error_message}"),
        }

    # Greet the user
    messages = []
    if response.full_name:
        messages.append(
            AIMessage(
                f"Welcome {response.full_name}!\n"
                f"I am UDA-Hub and I will be helping you on behalf of {account.get('account_name', account_id)}."
            )
        )

    # If this is the first interaction on behalf of the requested account let the user know.
    if response.uda_hub_user_created:
        messages.append(
            AIMessage(
                "It seems like I am serving you the first time. I created a new UDA Hub user for you to keep context.\n"
                f"Your user ID with me is {response.uda_hub_user_id}\n"
            )
        )

    return {
        "messages": messages,
        "is_validated": True,
        "has_pending_messages": True,
        "user": {
            "account_id": account_id,
            "account_name": account.get("account_name"),
            "account_description": account.get("account_description"),
            "external_user_id": external_user_id,
            "udahub_user_id": f"{response.uda_hub_user_id}",
            "full_name": f"{response.full_name}",
        },
    }
