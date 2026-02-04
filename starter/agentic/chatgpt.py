"""
Complete LangGraph example: Validation -> Enrichment -> Supervisor(loop) -> Workers -> Memorization

Features:
- Idempotent Validation/Enrichment (skips after first successful run)
- Supervisor routes to worker agents
- Workers can ask follow-up questions (awaiting_user) and continue on next user turn
- Checkpointing with MemorySaver + thread_id (conversation/session continuity)
- FastMCP is mocked here; replace MCPClient methods with your real calls

Requires:
  pip install langgraph

(Your LLM calls are mocked with simple heuristics in this example.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages


# -----------------------------
# Types
# -----------------------------

Route = Literal["faq", "reservation", "subscription", "handoff_human", "finish"]

TaskStatus = Literal[
    "needs_action",  # supervisor should route to a worker
    "awaiting_user",  # worker asked a question; stop until user answers
    "done",  # finished; memorize & end
    "error",  # error; optionally memorize & end
]


class UserCtx(TypedDict, total=False):
    user_id: str
    is_valid: bool
    enriched: bool
    subscription_status: str
    locale: str


class PendingAction(TypedDict, total=False):
    type: str  # e.g. "create_reservation"
    payload: Dict[str, Any]


class TaskCtx(TypedDict, total=False):
    status: TaskStatus
    final_answer: str
    question: str
    error: str
    pending: PendingAction


class GraphState(TypedDict):
    messages: List[Dict[str, Any]]
    user: UserCtx
    task: TaskCtx
    route: Optional[Route]
    trace: List[Dict[str, Any]]


# -----------------------------
# FastMCP mock (replace with real client)
# -----------------------------


@dataclass
class MCPClient:
    """Mocked tool client. Replace methods with real FastMCP tool calls."""

    def validate_user(self, user_id: str) -> bool:
        return bool(user_id) and user_id != "blocked"

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        return {"locale": "de-DE"}

    def get_subscription(self, user_id: str) -> Dict[str, Any]:
        return {"subscription_status": "active"}

    def create_reservation(
        self, user_id: str, date: str, time: str, party_size: int
    ) -> Dict[str, Any]:
        # In reality: call your reservation tool
        return {
            "reservation_id": "resv_123",
            "date": date,
            "time": time,
            "party_size": party_size,
        }

    def store_conversation(
        self, user_id: str, messages: List[Dict[str, Any]], trace: List[Dict[str, Any]]
    ) -> None:
        # In reality: write to DB / vector store / etc.
        pass


mcp = MCPClient()


# -----------------------------
# Helpers
# -----------------------------


def last_user_text(state: GraphState) -> str:
    for m in reversed(state["messages"]):
        if m.get("role") == "user":
            return m.get("content", "") or ""
    return ""


def set_task(state: GraphState, **updates: Any) -> GraphState:
    task = dict(state.get("task", {}))
    task.update(updates)
    return {**state, "task": task}


def append_trace(state: GraphState, event: Dict[str, Any]) -> GraphState:
    trace = list(state.get("trace", []))
    trace.append(event)
    return {**state, "trace": trace}


# -----------------------------
# Nodes
# -----------------------------


def validation_node(state: GraphState) -> GraphState:
    # Idempotent: skip if already valid
    user = dict(state.get("user", {}))
    if user.get("is_valid") is True:
        return state

    user_id = user.get("user_id", "")
    ok = mcp.validate_user(user_id)
    user["is_valid"] = ok

    if not ok:
        state = set_task(state, status="error", error="invalid_user")
        state = {**state, "user": user}
        state = append_trace(state, {"event": "validation_failed", "user_id": user_id})
        state["messages"] = add_messages(
            state["messages"],
            [
                {
                    "role": "assistant",
                    "content": "Ich konnte dich leider nicht authentifizieren.",
                }
            ],
        )
        return state

    state = {**state, "user": user}
    state = append_trace(state, {"event": "validated", "user_id": user_id})
    # Ensure task defaults
    if "task" not in state or "status" not in state["task"]:
        state = set_task(state, status="needs_action")
    return state


def enrichment_node(state: GraphState) -> GraphState:
    # Idempotent: skip if already enriched
    user = dict(state.get("user", {}))
    if user.get("enriched") is True:
        return state

    user_id = user.get("user_id", "")
    profile = mcp.get_user_profile(user_id)
    subs = mcp.get_subscription(user_id)

    user.update(profile)
    user.update(subs)
    user["enriched"] = True

    state = {**state, "user": user}
    state = append_trace(
        state, {"event": "enriched", "fields": list(profile.keys()) + list(subs.keys())}
    )
    return state


def supervisor_node(state: GraphState) -> GraphState:
    task = state.get("task", {})
    if task.get("status") in ("done", "error"):
        return {**state, "route": "finish"}

    # If a pending action exists, route back to the responsible worker
    pending = task.get("pending", {})
    if pending and pending.get("type") == "create_reservation":
        return {**state, "route": "reservation"}

    text = last_user_text(state).lower()

    # Very naive routing for demo. Replace with LLM function-call constrained to Route enum.
    if any(k in text for k in ["reserv", "buch", "tisch", "slot"]):
        route: Route = "reservation"
    elif any(k in text for k in ["abo", "subscription", "künd", "cancel"]):
        route = "subscription"
    elif any(k in text for k in ["mensch", "human", "support", "agent"]):
        route = "handoff_human"
    else:
        route = "faq"

    state = append_trace(state, {"event": "route", "route": route})
    return {**state, "route": route}


# --- Worker: FAQ ---


def faq_agent_node(state: GraphState) -> GraphState:
    # In reality: call LLM + toolset over MCP
    answer = "FAQ-Antwort (Demo). Wenn du eine Reservierung willst, sag mir Datum/Uhrzeit/Personen."
    state["messages"] = add_messages(
        state["messages"], [{"role": "assistant", "content": answer}]
    )
    state = set_task(state, status="done", final_answer=answer)
    return state


# --- Worker: Subscription ---


def subscription_agent_node(state: GraphState) -> GraphState:
    user = state.get("user", {})
    status = user.get("subscription_status", "unknown")
    answer = f"Dein Subscription-Status ist: {status}."
    state["messages"] = add_messages(
        state["messages"], [{"role": "assistant", "content": answer}]
    )
    state = set_task(state, status="done", final_answer=answer)
    return state


# --- Worker: Reservation (with follow-up / confirmation flow) ---


def reservation_agent_node(state: GraphState) -> GraphState:
    """
    Demonstrates:
    - slot filling
    - asking follow-up questions (awaiting_user)
    - confirmation step
    - resuming via task.pending
    """
    user_id = state.get("user", {}).get("user_id", "")
    task = dict(state.get("task", {}))
    pending = dict(task.get("pending", {}))
    text = last_user_text(state).strip()

    # If we are awaiting user response for an existing pending action:
    if pending and pending.get("type") == "create_reservation":
        payload = dict(pending.get("payload", {}))

        # Very naive confirmation parsing:
        t = text.lower()
        if any(w in t for w in ["ja", "yes", "ok", "passt", "confirm"]):
            res = mcp.create_reservation(
                user_id=user_id,
                date=payload["date"],
                time=payload["time"],
                party_size=payload["party_size"],
            )
            answer = (
                f"Alles klar — Reservierung bestätigt ✅\n"
                f"- Datum: {payload['date']}\n"
                f"- Uhrzeit: {payload['time']}\n"
                f"- Personen: {payload['party_size']}\n"
                f"- ID: {res['reservation_id']}"
            )
            state["messages"] = add_messages(
                state["messages"], [{"role": "assistant", "content": answer}]
            )
            # Clear pending action
            task.pop("pending", None)
            state = {**state, "task": task}
            state = set_task(state, status="done", final_answer=answer)
            return state

        if any(w in t for w in ["nein", "no", "doch nicht", "cancel", "abbrechen"]):
            answer = "Okay — dann sag mir bitte ein anderes Datum/Uhrzeit/Personen."
            state["messages"] = add_messages(
                state["messages"], [{"role": "assistant", "content": answer}]
            )
            task.pop("pending", None)
            state = {**state, "task": task}
            # Keep looping; we still need action
            state = set_task(state, status="needs_action")
            return state

        # If unclear response, ask again
        question = (
            "Bitte antworte mit **ja** (bestätigen) oder **nein** (ändern/abbrechen)."
        )
        state["messages"] = add_messages(
            state["messages"], [{"role": "assistant", "content": question}]
        )
        state = set_task(
            state, status="awaiting_user", question=question, pending=pending
        )
        return state

    # Otherwise: try to extract slots from free text (demo heuristics)
    # Expected example: "Reservierung am 2026-02-10 um 19:00 für 2"
    date = None
    time = None
    party_size = None

    tokens = text.replace(",", " ").split()

    # Super naive parsers:
    for tok in tokens:
        if len(tok) == 10 and tok[4] == "-" and tok[7] == "-":
            date = tok
        if len(tok) == 5 and tok[2] == ":" and tok[:2].isdigit() and tok[3:].isdigit():
            time = tok
        if tok.isdigit():
            n = int(tok)
            if 1 <= n <= 20:
                party_size = n

    missing = []
    if not date:
        missing.append("Datum (YYYY-MM-DD)")
    if not time:
        missing.append("Uhrzeit (HH:MM)")
    if not party_size:
        missing.append("Personenzahl")

    if missing:
        question = "Für die Reservierung brauche ich noch: " + ", ".join(missing) + "."
        state["messages"] = add_messages(
            state["messages"], [{"role": "assistant", "content": question}]
        )
        state = set_task(state, status="awaiting_user", question=question)
        return state

    # We have enough data -> ask for confirmation first (common pattern)
    payload = {"date": date, "time": time, "party_size": party_size}
    question = (
        f"Soll ich die Reservierung so anlegen?\n"
        f"- Datum: {date}\n"
        f"- Uhrzeit: {time}\n"
        f"- Personen: {party_size}\n\n"
        f"Antworte mit **ja** oder **nein**."
    )
    state["messages"] = add_messages(
        state["messages"], [{"role": "assistant", "content": question}]
    )
    state = set_task(
        state,
        status="awaiting_user",
        question=question,
        pending={"type": "create_reservation", "payload": payload},
    )
    return state


# --- Memorization ---


def memorization_node(state: GraphState) -> GraphState:
    user_id = state.get("user", {}).get("user_id", "")
    mcp.store_conversation(
        user_id=user_id, messages=state["messages"], trace=state.get("trace", [])
    )
    return append_trace(state, {"event": "memorized"})


# -----------------------------
# Routing functions (edges)
# -----------------------------


def gate_after_validation(state: GraphState) -> str:
    # If invalid -> end (we already wrote an assistant message)
    if state.get("task", {}).get("status") == "error":
        return "end"
    return "enrich"


def route_from_supervisor(state: GraphState) -> str:
    return state.get("route") or "faq"


def after_worker(state: GraphState) -> str:
    status = state.get("task", {}).get("status", "needs_action")
    if status == "awaiting_user":
        return "wait"
    if status in ("done", "error"):
        return "memorize"
    return "supervisor"


# -----------------------------
# Build graph
# -----------------------------


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("validation", validation_node)
    g.add_node("enrichment", enrichment_node)
    g.add_node("supervisor", supervisor_node)

    g.add_node("faq", faq_agent_node)
    g.add_node("reservation", reservation_agent_node)
    g.add_node("subscription", subscription_agent_node)

    g.add_node("memorize", memorization_node)

    g.set_entry_point("validation")

    g.add_conditional_edges(
        "validation",
        gate_after_validation,
        {
            "enrich": "enrichment",
            "end": END,
        },
    )

    g.add_edge("enrichment", "supervisor")

    g.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "faq": "faq",
            "reservation": "reservation",
            "subscription": "subscription",
            "handoff_human": END,
            "finish": "memorize",
        },
    )

    g.add_conditional_edges(
        "faq",
        after_worker,
        {
            "wait": END,
            "memorize": "memorize",
            "supervisor": "supervisor",
        },
    )
    g.add_conditional_edges(
        "reservation",
        after_worker,
        {
            "wait": END,
            "memorize": "memorize",
            "supervisor": "supervisor",
        },
    )
    g.add_conditional_edges(
        "subscription",
        after_worker,
        {
            "wait": END,
            "memorize": "memorize",
            "supervisor": "supervisor",
        },
    )

    g.add_edge("memorize", END)

    # Checkpointer makes multi-turn continuation possible via thread_id
    checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer)


# -----------------------------
# Demo runner (multi-turn)
# -----------------------------


def run_demo():
    app = build_graph()

    # This thread_id is your "conversation id" (store it per user/session)
    config = {"configurable": {"thread_id": "demo-thread-001"}}

    # Initial state (messages empty, user known)
    state: GraphState = {
        "messages": [],
        "user": {"user_id": "u_42"},
        "task": {"status": "needs_action"},
        "route": None,
        "trace": [],
    }

    print("Type messages. Try:")
    print('  "Ich will eine Reservierung am 2026-02-10 um 19:00 für 2"')
    print('  then answer "ja" to confirm.\n')

    while True:
        user_in = input("YOU: ").strip()
        if user_in.lower() in {"quit", "exit"}:
            break

        # Add user message to state
        state["messages"] = add_messages(
            state["messages"], [{"role": "user", "content": user_in}]
        )

        # Invoke graph
        state = app.invoke(state, config=config)

        # Print last assistant message (if any)
        assistant_msgs = [m for m in state["messages"] if m.get("role") == "assistant"]
        if assistant_msgs:
            print(f"BOT: {assistant_msgs[-1]['content']}\n")

        # If done, you could end the chat here; demo continues
        if state.get("task", {}).get("status") == "done":
            # reset status so user can continue asking new things in same thread
            state = set_task(state, status="needs_action")
        if state.get("task", {}).get("status") == "error":
            break


if __name__ == "__main__":
    run_demo()
