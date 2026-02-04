from typing import Optional
from pydantic import BaseModel, Field
from langchain.chat_models import BaseChatModel
from langchain.agents import create_agent
from langchain.messages import SystemMessage
from langgraph.errors import GraphRecursionError


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


async def user_validation_agent(
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
        result = await agent.ainvoke({}, config={"recursion_limit": 15})
        return result["structured_response"]

    except GraphRecursionError:
        return UserValidationResult(
            account_id=account_id,
            external_user_id=external_user_id,
            uda_hub_user_created=False,
            validation_successfull=False,
            error_message="An internal error occurred.",
        ).model_dump()
