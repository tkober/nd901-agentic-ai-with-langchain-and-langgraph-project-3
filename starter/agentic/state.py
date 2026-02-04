from typing import Literal, TypedDict
from langgraph.graph.message import MessagesState

TaskStatus = Literal["pending", "in_progress", "", "completed", "failed"]


class UserContext(TypedDict, total=False):
    account_id: str
    external_user_id: str
    udahub_user_id: str
    full_name: str


class TaskContext(TypedDict, total=False):
    status: TaskStatus
    error: str


class UdaHubState(MessagesState, total=False):
    ticket_id: str
    user: UserContext
    task: TaskContext
    is_validated: bool
    is_enriched: bool
