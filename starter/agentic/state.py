from typing import Literal, TypedDict, Optional
from langgraph.graph.message import MessagesState

TaskStatus = Literal["in_progress", "completed", "failed"]
Priority = Literal["normal", "high", "critical"]


class UserContext(TypedDict, total=False):
    account_id: str
    account_name: Optional[str]
    account_description: Optional[str]
    external_user_id: str
    udahub_user_id: str
    full_name: str
    udahub_user_created: bool


class TaskContext(TypedDict, total=False):
    status: TaskStatus
    error: str


class UdaHubState(MessagesState, total=False):
    user: UserContext
    task: TaskContext
    is_validated: bool
    is_enriched: bool
    terminate_chat: bool
    last_printed_idx: int
    has_pending_messages: bool
    need_user_input: bool
    handoff_requested: bool
    worker: Optional[str]
    priority: Optional[Priority]
    loaded_messages_count: Optional[int]
    ticket_for_continuation: Optional[str]
