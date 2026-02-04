from typing import Literal, Protocol, Optional, Sequence
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient, StreamableHttpConnection
from starter.agentic.state import UdaHubState, UserContext, TaskContext
from starter.agentic.agents.validation import validation_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

import asyncio
import uuid

load_dotenv()


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


def enrichment_agent(state: UdaHubState) -> UdaHubState:
    print("Called enrichment_agent")
    return state


class UdaHubAgent:
    def __build_graph(self):
        graph = StateGraph(UdaHubState)

        # Define Nodes
        graph.add_node(validation_agent, name="validation_agent")
        # graph.add_node(enrichment_agent, name="enrichment_agent")

        # Define Entry Point
        graph.set_entry_point("validation_agent")

        # Define Edges
        # graph.add_conditional_edges()

        checkpointer = MemorySaver()
        return graph.compile(checkpointer=checkpointer)

    def __build_mcp_client(self):
        return MultiServerMCPClient(
            {
                "udahub": StreamableHttpConnection(
                    url="http://localhost:8001/mcp", transport="streamable_http"
                ),
                "knowledge_base": StreamableHttpConnection(
                    url="http://localhost:8002/mcp", transport="streamable_http"
                ),
                "cultpass": StreamableHttpConnection(
                    url="http://localhost:8003/mcp", transport="streamable_http"
                ),
            }
        )

    def __init__(self):
        self.graph = self.__build_graph()
        self.mcp_client = self.__build_mcp_client()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
        )

    async def start_chat(
        self,
        account_id: str,
        exteranal_user_id: str,
        ticket_id: Optional[str] = None,
        thread_id: str = str(uuid.uuid4()),
        user_interface: UserInterface = ConsoleUserInterface(),
    ):
        print("Starting UdaHubAgent chat...")
        tools = await self.mcp_client.get_tools()

        state = UdaHubState(
            messages=[],
            user=UserContext(
                account_id=account_id,
                external_user_id=exteranal_user_id,
            ),
        )
        config = {
            "configurable": {
                "thread_id": thread_id,
                "mcp_tools": tools,
                "llm": self.llm,
            },
        }
        result_state = await self.graph.ainvoke(state, config=config)
        print(result_state)


if __name__ == "__main__":
    agent = UdaHubAgent()
    for i in range(1):
        asyncio.run(agent.start_chat("cultpass", "f556c0", thread_id="test"))
