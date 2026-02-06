from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session
from starter.data.models.udahub import User, Account, Ticket, TicketMetadata
from dotenv import load_dotenv

import os
import uuid


load_dotenv()

UDAHUB_DB_PATH = os.getenv("UDAHUB_DB_PATH", "sqlite:///starter/data/core/udahub.db")


def create_user(account_id: str, external_user_id: str, user_name: str) -> dict:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        new_user = User(
            user_id=str(uuid.uuid4()),
            account_id=account_id,
            external_user_id=external_user_id,
            user_name=user_name,
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
        return result


def get_user_by_id(user_id: str) -> dict | None:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        statement = select(User).where(User.user_id == user_id)
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return None

        result = {
            "user_id": result.user_id,
            "account_id": result.account_id,
            "external_user_id": result.external_user_id,
            "user_name": result.user_name,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }
        return result


def get_user_by_account_and_external_id(
    account_id: str, external_user_id: str
) -> dict | None:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        statement = select(User).where(
            User.account_id == account_id,
            User.external_user_id == external_user_id,
        )
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return None

        result = {
            "user_id": result.user_id,
            "account_id": result.account_id,
            "external_user_id": result.external_user_id,
            "user_name": result.user_name,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }
        return result


def get_account_by_id(account_id: str) -> dict | None:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        statement = select(Account).where(Account.account_id == account_id)
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return None

        result = {
            "account_id": result.account_id,
            "account_name": result.account_name,
            "account_description": result.account_description,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }
        return result


def create_ticket(
    account_id: str,
    user_id: str,
    channel: str,
    summary: str,
    status: str,
    tags: list[str],
) -> str:
    engine = create_engine(UDAHUB_DB_PATH)
    with Session(engine) as session:
        ticket_id = str(uuid.uuid4())
        new_ticket = Ticket(
            ticket_id=ticket_id,
            account_id=account_id,
            user_id=user_id,
            channel=channel,
            summary=summary,
        )
        session.add(new_ticket)

        new_metadata = TicketMetadata(
            ticket_id=ticket_id,
            status=status,
            tags=",".join(tags),
        )
        session.add(new_metadata)
        session.commit()

        return ticket_id
