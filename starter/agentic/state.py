from typing import Literal, TypedDict
from langgraph.graph.message import MessagesState

TaskStatus = Literal["pending", "in_progress", "", "completed", "failed"]


class UserContext(TypedDict, total=False):
    account_id: str
    user_id: str


class TaskContext(TypedDict, total=False):
    status: TaskStatus
    error: str


class UdaHubState(MessagesState, total=False):
    udahub_user_id: str
    ticket_id: str
    user: UserContext
    task: TaskContext
    is_validated: bool
    enriched: bool
