from pydantic import BaseModel, Field
from langchain.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langchain.messages import AIMessage, SystemMessage
from langgraph.errors import GraphRecursionError
from starter.agentic.state import UdaHubState, UserContext, TaskContext
from langchain_mcp_adapters.client import MultiServerMCPClient
from starter.agentic.mcp_tool_utils import McpToolFilter


class UserValidationResult(BaseModel):
    account_id: str = Field(description="The account ID of the UDA Hub customer")
    uda_hub_user_id: str = Field(description="The users ID in UDA Hubs system")
    external_user_id: str = Field(description="The users ID in the customers system")
    uda_hub_user_created: bool = Field(
        description="A flag that shows whether a new UDA Hub user had to be created",
        default=False,
    )
    validation_successfull: bool = Field(
        description="A flag that shows whether the user could be validated with the customer",
        default=False,
    )
    error_message: str = Field(
        description="The error message in case the validation failed"
    )


async def validate_user(
    llm: BaseChatModel, tools: list, account_id: str, user_id: str
) -> dict:
    agent = create_agent(
        model=llm,
        system_prompt=SystemMessage(f"""
        You are a validation agent for UDA Hub. You need to validate a user for the customer with the account_id='{account_id}'.
        It has already been checked, that {account_id} is a legit customer of UDA Hub. 

        The user with the user_id='{user_id}' needs to be validated using the following steps:

        1.) Check with the customer whether with user exists and get the details. If the user does not exist stop here.
        2.) Check with UDA Hub MCP Server whether they already have a corresponding user in their DB.
        3.) If UDA Hub does not have an corresponding entry yet, create one with the details you got from the customer.
        """),
        tools=tools,
        response_format=UserValidationResult,
    )

    try:
        result = await agent.ainvoke({}, config={"recursion_limit": 15})
        return result["structured_response"]

    except GraphRecursionError:
        return UserValidationResult(
            account_id=account_id,
            external_user_id=user_id,
            uda_hub_user_id="",
            uda_hub_user_created=False,
            validation_successfull=False,
            error_message="An internal error occurred.",
        ).model_dump()


async def validation_agent(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    if state.get("is_validated", False) is True:
        return state

    tools = config.get("configurable", {}).get("mcp_tools", [])
    llm = config.get("configurable", {}).get("llm")
    account_id = state.get("user", {}).get("account_id", "")
    user_id = state.get("user", {}).get("user_id", "")

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
    validation_tools.extend(McpToolFilter(tools).by_author("UDA Hub").get_all())
    validation_tools.extend(
        McpToolFilter(tools).by_author(account_id).by_read_only(True).get_all()
    )
    response = await validate_user(
        llm=llm, tools=validation_tools, account_id=account_id, user_id=user_id
    )
    print(response)

    print("Called validation_agent")
    return state
