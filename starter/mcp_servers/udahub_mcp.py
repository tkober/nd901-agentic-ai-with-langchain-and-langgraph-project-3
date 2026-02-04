from sqlalchemy import select, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from starter.data.models.udahub import User, Account, Ticket
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import os
import uuid


load_dotenv()
logger = get_logger("udahub_mcp")

mcp = FastMCP("UDA Hub MCP Server")

UDAHUB_DB_PATH = os.getenv("UDAHUB_DB_PATH", "sqlite:///starter/data/core/udahub.db")
UDAHUB_MCP_PORT = int(os.getenv("CULTPASS_MCP_PORT", "8001"))


class CreateUdaHubUserArguments(BaseModel):
    account_id: str = Field(
        description="The ID of the account to which the user belongs."
    )
    external_user_id: str = Field(description="The external ID of the user.")
    user_name: str = Field(description="The name of the user.")


@mcp.tool(
    name="create_udahub_user",
    description="Create a new user in the UdaHub database.",
    tags=set(["udahub", "user", "create"]),
    meta={"author": "UDAHub", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
)
def create_udahhub_user(user: CreateUdaHubUserArguments) -> dict:
    engine = create_engine(UDAHUB_DB_PATH)
    try:
        with Session(engine) as session:
            new_user = User(
                user_id=str(uuid.uuid4()),
                account_id=user.account_id,
                external_user_id=user.external_user_id,
                user_name=user.user_name,
            )
            session.add(new_user)
            session.commit()
            result = {
                "user_id": new_user.user_id,
                "account_id": new_user.account_id,
                "external_user_id": new_user.external_user_id,
                "user_name": new_user.user_name,
                "created_at": new_user.created_at.isoformat(),
                "updated_at": new_user.updated_at.isoformat(),
            }
            logger.debug(f"Created new UdaHub user: {result}")
            return result

    except IntegrityError as e:
        logger.error(f"Integrity error creating UdaHub user: {e}")
        return {
            "error": "User with the given external_user_id and account_id already exists."
        }


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
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        statement = select(User).where(User.user_id == user.user_id)
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            logger.debug(f"UdaHub user with ID {user.user_id} not found.")
            return None

        result = {
            "user_id": result.user_id,
            "account_id": result.account_id,
            "external_user_id": result.external_user_id,
            "user_name": result.user_name,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }
        logger.debug(f"Retrieved UdaHub user: {result}")
        return result


class GetFindUdaHubUserArguments(BaseModel):
    account_id: str = Field(description="The account id of the customer")
    external_user_id: str = Field(description="The user ID in the customers system")


@mcp.tool(
    name="find_udahub_user",
    description="Find a user in the UdaHub database by using the account ID of a customer and the external user ID.",
    tags=set(["udahub", "user", "details"]),
    meta={"author": "UDAHub", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def find_external_user(user: GetFindUdaHubUserArguments) -> dict | None:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        statement = select(User).where(
            User.account_id == user.account_id,
            User.external_user_id == user.external_user_id,
        )
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            logger.debug(
                f"UdaHub user with account ID {user.account_id} and external user ID {user.external_user_id} not found."
            )
            return None

        result = {
            "user_id": result.user_id,
            "account_id": result.account_id,
            "external_user_id": result.external_user_id,
            "user_name": result.user_name,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }
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
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        statement = select(Account).where(Account.account_id == account.account_id)
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            logger.debug(f"UdaHub account with ID {account.account_id} not found.")
            return None

        result = {
            "account_id": result.account_id,
            "account_name": result.account_name,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }
        logger.debug(f"Retrieved UdaHub account: {result}")
        return result


if __name__ == "__main__":
    mcp.run(transport="http", port=UDAHUB_MCP_PORT, log_level="debug")
