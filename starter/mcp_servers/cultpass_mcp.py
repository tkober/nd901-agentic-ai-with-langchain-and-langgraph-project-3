from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session, selectinload
from starter.data.models.cultpass import User, Reservation, Experience
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

import os

load_dotenv()
logger = get_logger("udahub_mcp")

mcp = FastMCP("Cultpass MCP Server")

CULTPASS_DB_PATH = os.getenv(
    "CULTPASS_DB_PATH", "sqlite:///starter/data/external/cultpass.db"
)
CULTPASS_MCP_PORT = int(os.getenv("CULTPASS_MCP_PORT", "8003"))


class GetUserArguments(BaseModel):
    user_id: str = Field(description="The ID of the user to retrieve.")


def checked_date(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def yield_error(error_message: str) -> dict:
    logger.debug(error_message)
    return {"error": error_message}


def yield_message(message: str) -> dict:
    logger.debug(message)
    return {"message": message}


@mcp.tool(
    name="get_cultpass_user",
    description="Retrieve user details from the Cultpass database.",
    tags=set(["cultpass", "user", "details", "subscription", "validation"]),
    meta={"author": "cultpass", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def get_cultpass_user(user: GetUserArguments) -> dict:
    engine = create_engine(CULTPASS_DB_PATH)
    with Session(engine) as session:
        statement = (
            select(User)
            .where(User.user_id == user.user_id)
            .options(selectinload(User.subscription))
        )
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return yield_error(f"No Cultpass user found for user_id {user.user_id}")

        result = {
            "user_id": result.user_id,
            "full_name": result.full_name,
            "email": result.email,
            "is_blocked": result.is_blocked,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
            "subscription": {
                "subscription_id": result.subscription.subscription_id,
                "user_id": result.subscription.user_id,
                "status": result.subscription.status,
                "tier": result.subscription.tier,
                "monthly_quota": result.subscription.monthly_quota,
                "started_at": result.subscription.started_at.isoformat(),
                "ended_at": checked_date(result.subscription.ended_at),
                "created_at": result.subscription.created_at.isoformat(),
                "updated_at": result.subscription.updated_at.isoformat(),
            },
        }
        logger.debug(f"Retrieved Cultpass user: {result}")
        return result


@mcp.tool(
    name="cancel_cultpass_subscription",
    description="Cancel a user's subscription in the Cultpass database.",
    tags=set(["cultpass", "subscription", "cancel"]),
    meta={"author": "cultpass", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
    },
)
def cancel_subscription(user: GetUserArguments) -> dict:
    engine = create_engine(CULTPASS_DB_PATH)
    with Session(engine) as session:
        statement = (
            select(User)
            .where(User.user_id == user.user_id)
            .options(selectinload(User.subscription))
        )
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return yield_error(f"No Cultpass user found for user_id {user.user_id}")

        if result.subscription is None or result.subscription.status != "active":
            return yield_error("User does not have an active subscription.")

        result.subscription.status = "cancelled"
        result.subscription.ended_at = datetime.utcnow()
        session.commit()

    return yield_message("Subscription cancelled successfully.")


@mcp.tool(
    name="reactivate_cultpass_subscription",
    description="Reactivate a user's cancelled subscription in the Cultpass database.",
    tags=set(["cultpass", "subscription", "reactivate"]),
    meta={"author": "cultpass", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
)
def reactivate_subscription(user: GetUserArguments) -> dict:
    engine = create_engine(CULTPASS_DB_PATH)
    with Session(engine) as session:
        statement = (
            select(User)
            .where(User.user_id == user.user_id)
            .options(selectinload(User.subscription))
        )
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return yield_error(f"No Cultpass user found for user_id {user.user_id}")

        if result.subscription is None or result.subscription.status != "cancelled":
            return yield_error("User does not have a cancelled subscription.")

        result.subscription.status = "active"
        result.subscription.ended_at = None
        session.commit()

    return yield_message("Subscription reactivated successfully.")


@mcp.tool(
    name="upgrade_cultpass_subscription",
    description="Upgrade a user's subscription to premium in the Cultpass database.",
    tags=set(["cultpass", "subscription", "upgrade"]),
    meta={"author": "cultpass", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
)
def upgrade_subscription(user: GetUserArguments) -> dict:
    engine = create_engine(CULTPASS_DB_PATH)
    with Session(engine) as session:
        statement = (
            select(User)
            .where(User.user_id == user.user_id)
            .options(selectinload(User.subscription))
        )
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return yield_error(f"No Cultpass user found for user_id {user.user_id}")

        if result.subscription is None or result.subscription.status != "active":
            return yield_error("User does not have an active subscription.")

        if result.subscription.tier == "premium":
            return yield_error("User already has a premium subscription.")

        result.subscription.tier = "premium"
        session.commit()

    return yield_message("Subscription upgraded to premium successfully.")


@mcp.tool(
    name="get_cultpass_reservations",
    description="Retrieve reservations for a user from the Cultpass database.",
    tags=set(["cultpass", "reservation", "details"]),
    meta={"author": "cultpass", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def get_reservations(user: GetUserArguments) -> list[dict]:
    engine = create_engine(CULTPASS_DB_PATH)
    with Session(engine) as session:
        statement = (
            select(Reservation)
            .where(Reservation.user_id == user.user_id)
            .options(selectinload(Reservation.experience))
        )
        results = session.execute(statement).scalars().all()
        reservations = []
        for result in results:
            reservations.append(
                {
                    "reservation_id": result.reservation_id,
                    "user_id": result.user_id,
                    "experience_id": result.experience_id,
                    "status": result.status,
                    "created_at": result.created_at.isoformat(),
                    "updated_at": result.updated_at.isoformat(),
                    "experience": {
                        "experience_id": result.experience.experience_id,
                        "title": result.experience.title,
                        "description": result.experience.description,
                        "location": result.experience.location,
                        "when": result.experience.when.isoformat(),
                        "is_premium": result.experience.is_premium,
                    },
                }
            )

        logger.debug(f"Retrieved reservations: {reservations}")
        return reservations


class CancelReservationArguments(BaseModel):
    user_id: str = Field(description="The ID of the user cancelling the reservation.")
    reservation_id: str = Field(description="The ID of the reservation to cancel.")


@mcp.tool(
    name="cancel_cultpass_reservation",
    description="Cancel a reservation for a user in the Cultpass database.",
    tags=set(["cultpass", "reservation", "cancel"]),
    meta={"author": "cultpass", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
    },
)
def cancel_reservation(reservation: CancelReservationArguments) -> dict:
    engine = create_engine(CULTPASS_DB_PATH)
    with Session(engine) as session:
        statement = (
            select(Reservation)
            .where(
                Reservation.reservation_id == reservation.reservation_id,
                Reservation.user_id == reservation.user_id,
            )
            .options(selectinload(Reservation.experience))
        )
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return yield_error("Reservation not found.")

        if result.status == "cancelled":
            return yield_error("Reservation is already cancelled.")

        result.status = "cancelled"
        result.experience.slots_available += 1
        session.commit()

    return yield_message("Reservation cancelled successfully.")


class MakeReservationArguments(BaseModel):
    user_id: str = Field(description="The ID of the user making the reservation.")
    experience_id: str = Field(description="The ID of the experience to reserve.")


@mcp.tool(
    name="make_cultpass_reservation",
    description="Make a reservation for a user in the Cultpass database.",
    tags=set(["cultpass", "reservation", "create"]),
    meta={"author": "cultpass", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
)
def make_reservation(reservation: MakeReservationArguments) -> dict:
    engine = create_engine(CULTPASS_DB_PATH)
    with Session(engine) as session:
        user_statement = (
            select(User)
            .where(User.user_id == reservation.user_id)
            .options(selectinload(User.subscription))
        )
        user = session.execute(user_statement).scalar_one_or_none()
        if user is None:
            return yield_error("User not found.")

        if user.is_blocked:
            return yield_error("User is blocked from making reservations.")

        if user.subscription is None or user.subscription.status != "active":
            return yield_error("User does not have an active subscription.")

        reservation_statement = select(Reservation).where(
            Reservation.user_id == reservation.user_id,
            Reservation.experience_id == reservation.experience_id,
            Reservation.status != "cancelled",
        )
        existing_reservation = session.execute(
            reservation_statement
        ).scalar_one_or_none()
        if existing_reservation is not None:
            return yield_error("User already has a reservation for this experience.")

        experience_statement = select(Experience).where(
            Experience.experience_id == reservation.experience_id
        )
        experience = session.execute(experience_statement).scalar_one_or_none()

        if experience is None:
            return yield_error("Experience not found.")

        if experience.slots_available <= 0:
            return yield_error("No slots available for this experience.")

        if experience.is_premium and user.subscription.tier != "premium":
            return yield_error(
                "Experience is premium and user does not have a premium subscription."
            )

        new_reservation = Reservation(
            reservation_id=os.urandom(8).hex(),
            user_id=reservation.user_id,
            experience_id=reservation.experience_id,
            status="reserved",
        )
        experience.slots_available -= 1
        session.add(new_reservation)
        session.commit()

        return {
            "reservation_id": new_reservation.reservation_id,
            "user_id": new_reservation.user_id,
            "experience_id": new_reservation.experience_id,
            "status": new_reservation.status,
            "created_at": new_reservation.created_at.isoformat(),
            "updated_at": new_reservation.updated_at.isoformat(),
        }


class GetExperienceArguments(BaseModel):
    experience_id: str = Field(description="The ID of the experience to retrieve.")


@mcp.tool(
    name="get_cultpass_experience",
    description="Retrieve experience details from the Cultpass database.",
    tags=set(["cultpass", "experience", "details", "browsing"]),
    meta={"author": "cultpass", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def get_experience(experience: GetExperienceArguments) -> dict:
    engine = create_engine(CULTPASS_DB_PATH)
    with Session(engine) as session:
        statement = select(Experience).where(
            Experience.experience_id == experience.experience_id
        )
        result = session.execute(statement).scalar_one_or_none()
        if result is None:
            return yield_error(
                f"No experience found for experience_id {experience.experience_id}"
            )

        return {
            "experience_id": result.experience_id,
            "title": result.title,
            "description": result.description,
            "location": result.location,
            "when": result.when.isoformat(),
            "slots_available": result.slots_available,
            "is_premium": result.is_premium,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }


if __name__ == "__main__":
    mcp.run(transport="http", port=CULTPASS_MCP_PORT, log_level="debug")
