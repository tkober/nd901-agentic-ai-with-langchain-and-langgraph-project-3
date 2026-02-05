from sqlalchemy.exc import IntegrityError
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from starter.data.udahub_db import (
    create_user,
    get_user_by_id,
    get_user_by_account_and_external_id,
    get_account_by_id,
)

import os


load_dotenv()
logger = get_logger("udahub_mcp")

mcp = FastMCP("UDA Hub MCP Server")

UDAHUB_DB_PATH = os.getenv("UDAHUB_DB_PATH", "sqlite:///starter/data/core/udahub.db")
UDAHUB_MCP_PORT = int(os.getenv("UDAHUB_MCP_PORT", "8001"))


def yield_error(error_message: str) -> dict:
    logger.debug(error_message)
    return {"error": error_message}


def yield_message(message: str) -> dict:
    logger.debug(message)
    return {"message": message}


class CreateUdaHubUserArguments(BaseModel):
    account_id: str = Field(
        description="The ID of the account to which the user belongs."
    )
    external_user_id: str = Field(description="The external ID of the user.")
    user_name: str = Field(description="The name of the user.")


@mcp.tool(
    name="create_udahub_user",
    description="Create a new user in the UdaHub database.",
    tags=set(["udahub", "user", "create", "validation"]),
    meta={"author": "UDAHub", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
)
def create_udahhub_user(user: CreateUdaHubUserArguments) -> dict:
    try:
        result = create_user(
            account_id=user.account_id,
            external_user_id=user.external_user_id,
            user_name=user.user_name,
        )
        logger.debug(f"Created new UdaHub user: {result}")
        return result

    except IntegrityError as e:
        logger.error(f"Integrity error creating UdaHub user: {e}")
        return yield_error(
            "User with the given external_user_id and account_id already exists."
        )


class GetUdaHubUserArguments(BaseModel):
    user_id: str = Field(description="The ID of the user to retrieve.")


@mcp.tool(
    name="get_udahub_user",
    description="Retrieve user details from the UdaHub database by using the internal UDA Hub user ID.",
    tags=set(["udahub", "user", "details"]),
    meta={"author": "UDAHub", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def get_udahub_user(user: GetUdaHubUserArguments) -> dict | None:
    result = get_user_by_id(user.user_id)
    if result is None:
        logger.debug(f"UdaHub user with ID {user.user_id} not found.")
        return None

    logger.debug(f"Retrieved UdaHub user: {result}")
    return result


class GetFindUdaHubUserArguments(BaseModel):
    account_id: str = Field(description="The account id of the customer")
    external_user_id: str = Field(description="The user ID in the customers system")


@mcp.tool(
    name="find_udahub_user",
    description="Find a user in the UdaHub database by using the account ID of a customer and the external user ID.",
    tags=set(["udahub", "user", "details", "validation"]),
    meta={"author": "UDAHub", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def find_external_user(user: GetFindUdaHubUserArguments) -> dict | None:
    result = get_user_by_account_and_external_id(
        account_id=user.account_id, external_user_id=user.external_user_id
    )
    if result is None:
        logger.debug(
            f"UdaHub user with account ID {user.account_id} and external user ID {user.external_user_id} not found."
        )
        return None

    logger.debug(f"Retrieved UdaHub user: {result}")
    return result


class GetUdaHubAccountArguments(BaseModel):
    account_id: str = Field(description="The ID of the account to retrieve.")


@mcp.tool(
    name="get_udahub_account",
    description="Retrieve account details from the UdaHub database.",
    tags=set(["udahub", "account", "details"]),
    meta={"author": "UDAHub", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def get_udahub_account(account: GetUdaHubAccountArguments) -> dict | None:
    result = get_account_by_id(account.account_id)
    if result is None:
        logger.debug(f"UdaHub account with ID {account.account_id} not found.")
        return None

    logger.debug(f"Retrieved UdaHub account: {result}")
    return result


if __name__ == "__main__":
    mcp.run(transport="http", port=UDAHUB_MCP_PORT, log_level="debug")
