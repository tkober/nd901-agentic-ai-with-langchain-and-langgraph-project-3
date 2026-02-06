from typing import Optional, TypedDict, Protocol, Awaitable
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient, StreamableHttpConnection
from langchain_mcp_adapters.sessions import Connection
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.graph import MermaidDrawMethod
from starter.agentic.state import UdaHubState, UserContext
from starter.agentic.nodes.knowledgebase_sync import knowledgebase_sync_node
from starter.agentic.nodes.validation import validation_node
from starter.agentic.nodes.enrichment import enrichment_node
from starter.agentic.nodes.supervisor import supervisor_node
from starter.agentic.nodes.memorization import memorization_node
from starter.agentic.nodes.send_messages import send_message_node
from starter.agentic.nodes.read_message import read_message_node
from starter.agentic.agents.browsing import browsing_agent_node
from starter.agentic.agents.escalate_to_human import escalate_to_human_agent_node
from starter.agentic.agents.faq import faq_agent_node
from starter.agentic.agents.reservation import reservation_agent_node
from starter.agentic.agents.subscription import subscription_agent_node
from starter.agentic.chat_interface import ChatInterface, ConsoleChatInterface
from langchain_openai import ChatOpenAI
from IPython.display import Image
from dotenv import load_dotenv

import asyncio
import uuid

load_dotenv()


class McpServerList:
    servers: dict[str, Connection]

    def __init__(self):
        self.servers = {}

    def add_connection(self, name: str, connection: Connection) -> "McpServerList":
        self.servers[name] = connection
        return self

    def create_client(self) -> MultiServerMCPClient:
        return MultiServerMCPClient(self.servers)


class AgentAction(Protocol):
    def __call__(
        self, state: UdaHubState, config: RunnableConfig
    ) -> UdaHubState | Awaitable[UdaHubState]: ...


class UdaHubAgent(TypedDict):
    name: str
    description: str
    action: AgentAction


def not_yet_implemented(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    print("Not yet implemented")
    return state


FAQ_AGENT = UdaHubAgent(
    name="faq",
    description="An agent that answers common questions.",
    action=faq_agent_node,
)
RESERVATION_AGENT = UdaHubAgent(
    name="reservation",
    description="An agent that handles everything related to reservations.",
    action=reservation_agent_node,
)
SUBSCRIPTION_AGENT = UdaHubAgent(
    name="subscription",
    description="An agent that handles everything related to a users subscription.",
    action=subscription_agent_node,
)
BROWSING_AGENT = UdaHubAgent(
    name="browsing",
    description="An agent that helps browsing through the offerings of a customer.",
    action=browsing_agent_node,
)

DEFAULT_AGENT_SET = [
    FAQ_AGENT,
    RESERVATION_AGENT,
    SUBSCRIPTION_AGENT,
    BROWSING_AGENT,
]


class UdaHubAgent:
    def __init__(
        self,
        mcp_servers: McpServerList = McpServerList(),
        agents: list[UdaHubAgent] = DEFAULT_AGENT_SET,
        openai_model: str = "gpt-4.1",
    ):
        self.agents = agents
        self.graph = self._build_graph()
        self.mcp_client = self._build_mcp_client(mcp_servers)
        self.llm = ChatOpenAI(
            model=openai_model,  # ty:ignore[unknown-argument]
            temperature=0.0,
        )

    def _build_graph(self):
        graph = StateGraph(UdaHubState)  # ty:ignore[invalid-argument-type]

        # Define Nodes
        graph.add_node(node="knowledgebase_sync", action=knowledgebase_sync_node)
        graph.add_node(node="validation", action=validation_node)
        graph.add_node(node="enrichment", action=enrichment_node)
        graph.add_node(node="supervisor", action=supervisor_node)
        graph.add_node(node="escalate_to_human", action=escalate_to_human_agent_node)

        for agent in self.agents:
            graph.add_node(node=agent["name"], action=agent["action"])

        graph.add_node(node="memorize", action=memorization_node)
        graph.add_node(node="read_message", action=read_message_node)
        graph.add_node(node="send_message", action=send_message_node)

        # Define Edges
        graph.add_edge(START, "knowledgebase_sync")
        graph.add_edge("knowledgebase_sync", "validation")
        graph.add_edge("validation", "enrichment")
        graph.add_edge("enrichment", "supervisor")

        supervisor_path_map = {agent["name"]: agent["name"] for agent in self.agents}
        supervisor_path_map["escalate_to_human"] = "escalate_to_human"
        supervisor_path_map["read_message"] = "read_message"
        supervisor_path_map["send_message"] = "send_message"
        supervisor_path_map["end"] = "memorize"
        graph.add_conditional_edges(
            source="supervisor",
            path=self._supervisor_handoff,
            path_map=supervisor_path_map,
        )

        for agent in self.agents:
            graph.add_edge(agent["name"], "supervisor")

        graph.add_edge("read_message", "supervisor")
        graph.add_edge("send_message", "supervisor")
        graph.add_edge("escalate_to_human", "supervisor")
        graph.add_edge("memorize", END)

        checkpointer = MemorySaver()
        return graph.compile(checkpointer=checkpointer)

    def _supervisor_handoff(self, state: UdaHubState) -> str:
        return state.get("worker") or "escalate_to_human"

    def _build_mcp_client(self, mcp_servers: McpServerList):
        return (
            mcp_servers.add_connection(
                "udahub",
                StreamableHttpConnection(
                    url="http://localhost:8001/mcp", transport="streamable_http"
                ),
            )
            .add_connection(
                "knowledge_base",
                StreamableHttpConnection(
                    url="http://localhost:8002/mcp", transport="streamable_http"
                ),
            )
            .create_client()
        )

    def draw_graph_as_mermaid(self) -> Image:
        return Image(
            self.graph.get_graph().draw_mermaid_png(
                draw_method=MermaidDrawMethod.PYPPETEER
            )
        )

    def print_graph_as_ascii(self):
        self.graph.get_graph().print_ascii()

    async def start_chat(
        self,
        account_id: str,
        exteranal_user_id: str,
        ticket_id: Optional[str] = None,
        thread_id: str = str(uuid.uuid4()),
        chat_interface: ChatInterface = ConsoleChatInterface(),
    ):
        print("(You can quit the chat by sending an empty message)\n")
        tools = await self.mcp_client.get_tools()
        print("\nStarting UDA Hub chat...")

        state = UdaHubState(
            messages=[],
            user=UserContext(
                account_id=account_id,
                external_user_id=exteranal_user_id,
            ),
            need_user_input=True,
        )
        available_agents = {
            agent["name"]: agent["description"] for agent in self.agents
        }
        config = {
            "configurable": {
                "thread_id": thread_id,
                "mcp_tools": tools,
                "llm": self.llm,
                "chat_interface": chat_interface,
                "available_agents": available_agents,
                "ticket_id": ticket_id,
            },
            "recursion_limit": 100,
        }

        print(f"Thread ID: {thread_id}\n")
        state = await self.graph.ainvoke(state, config=config)


if __name__ == "__main__":
    mcp_servers = McpServerList().add_connection(
        "cultpass",
        StreamableHttpConnection(
            url="http://localhost:8003/mcp", transport="streamable_http"
        ),
    )
    agent = UdaHubAgent(mcp_servers)
    for i in range(1):
        asyncio.run(
            agent.start_chat(
                account_id="cultpass",
                exteranal_user_id="f556c0",
                thread_id="test_thread",
            )
        )
