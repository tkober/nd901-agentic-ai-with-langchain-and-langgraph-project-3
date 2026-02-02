from typing import Literal, Protocol, Optional, Sequence
from langgraph.graph.message import MessagesState
from langgraph.types import Command
from langgraph.graph import START, END, StateGraph
from langgraph.types import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage


class UserInterface(Protocol):
    def next_message(self) -> Optional[str]:
        """Return next user message, or None if the stream is finished."""


class ListUserInterface:
    messages: Sequence[str]
    _i: int = 0

    def next_message(self) -> Optional[str]:
        if self._i >= len(self.messages):
            return None
        msg = self.messages[self._i]
        self._i += 1
        return msg


class ConsoleUserInterface:
    def next_message(self) -> str | None:
        msg = input("> ").strip()
        if msg.lower() in {"exit", "quit"}:
            return None
        return msg


class UdaHubState(MessagesState):
    enriched: bool


def validation_agent(
    state: UdaHubState,
) -> Command[Literal["enrichment_agent", "supervisor_agent", END]]:
    print("Called validation_agent")
    if state["enriched"]:
        return Command(goto="supervisor_agent")

    return Command(goto="enrichment_agent")


def enrichment_agent(state: UdaHubState) -> Command[Literal["supervisor_agent"]]:
    print("Called enrichment_agent")
    return Command(
        goto="supervisor_agent",
        update={"enriched": True},
    )


def supervisor_agent(
    state: UdaHubState, config: RunnableConfig
) -> Command[Literal["memorization_agent"]]:
    settings = config.get("configurable", {})
    ui: UserInterface = settings.get("user_interface") or ConsoleUserInterface()

    messages: list[HumanMessage] = []

    message = ui.next_message()
    while message is not None:
        messages.append(HumanMessage(content=message))
        message = ui.next_message()

    print("Called supervisor_agent")
    return Command(
        goto="memorization_agent",
        update={
            "messages": messages,
        },
    )


def memorization_agent(state: UdaHubState) -> Command[Literal[END]]:
    print("Called memorization_agent")
    return Command(goto=END)


workflow = StateGraph(UdaHubState)
workflow.add_node(validation_agent)
workflow.add_node(enrichment_agent)
workflow.add_node(supervisor_agent)
workflow.add_node(memorization_agent)

workflow.add_edge(START, "validation_agent")
graph = workflow.compile(
    checkpointer=MemorySaver(),
)
graph.invoke(
    input={"enriched": False},
    config={
        "configurable": {"thread_id": 4711, "user_interface": ConsoleUserInterface()}
    },
)
