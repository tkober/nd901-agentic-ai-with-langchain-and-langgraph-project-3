from starter.data.models.cultpass import User, Subscription
from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session, selectinload
from langchain_core.tools import tool
from starter.data.models.cultpass import User

cultpass_db = "starter/data/external/cultpass.db"
engine = create_engine(f"sqlite:///{cultpass_db}", echo=False)


@tool
def retrieve_user_details(user_id: str) -> User | None:
    """ """
    with Session(engine) as session:
        statement = (
            select(User)
            .where(User.user_id == user_id)
            .options(
                selectinload(User.subscription),
                selectinload(User.reservations),
            )
        )
        return session.execute(statement).scalar_one_or_none()


if __name__ == "__main__":
    user = retrieve_user_details("f556c0")
    print(user)
    print(user.subscription)
