from starter.data.models.udahub import User
from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session
from langchain_core.tools import tool
from starter.data.models.udahub import User


udahub_db = "starter/data/core/udahub.db"
engine = create_engine(f"sqlite:///{udahub_db}", echo=False)


@tool
def get_user_by_id(user_id: str) -> User | None:
    """ """
    with Session(engine) as session:
        statement = select(User).where(User.user_id == user_id)
        return session.execute(statement).scalar_one_or_none()


# if __name__ == "__main__":
#     user = get_user_by_id("c9757082-b360-4a23-b987-a13650aba26c")
#     print(user)
