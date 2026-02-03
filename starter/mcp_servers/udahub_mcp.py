from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session, selectinload
from starter.data.models.udahub import User, Account, Ticket
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import os
import uuid

load_dotenv()

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
)
def create_udahhub_user(user: CreateUdaHubUserArguments) -> dict:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        new_user = User(
            user_id=str(uuid.uuid4()),
            account_id=user.account_id,
            external_user_id=user.external_user_id,
            user_name=user.user_name,
        )
        session.add(new_user)
        session.commit()
        return {
            "user_id": new_user.user_id,
            "account_id": new_user.account_id,
            "external_user_id": new_user.external_user_id,
            "user_name": new_user.user_name,
            "created_at": new_user.created_at.isoformat(),
            "updated_at": new_user.updated_at.isoformat(),
        }


class GetUdaHubUserArguments(BaseModel):
    user_id: str = Field(description="The ID of the user to retrieve.")


@mcp.tool(
    name="get_udahub_user",
    description="Retrieve user details from the UdaHub database.",
    tags=set(["udahub", "user", "details"]),
)
def get_udahub_user(user: GetUdaHubUserArguments) -> dict | None:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        statement = select(User).where(User.user_id == user.user_id)
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return None

        return {
            "user_id": result.user_id,
            "account_id": result.account_id,
            "external_user_id": result.external_user_id,
            "user_name": result.user_name,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }


class GetUdaHubAccountArguments(BaseModel):
    account_id: str = Field(description="The ID of the account to retrieve.")


@mcp.tool(
    name="get_udahub_account",
    description="Retrieve account details from the UdaHub database.",
    tags=set(["udahub", "account", "details"]),
)
def get_udahub_account(account: GetUdaHubAccountArguments) -> dict | None:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        statement = select(Account).where(Account.account_id == account.account_id)
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return None

        return {
            "account_id": result.account_id,
            "account_name": result.account_name,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }


if __name__ == "__main__":
    mcp.run(transport="http", port=UDAHUB_MCP_PORT)
