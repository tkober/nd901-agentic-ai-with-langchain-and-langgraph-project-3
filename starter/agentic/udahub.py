from typing import Optional
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain.messages import HumanMessage
from langgraph.graph.message import add_messages
from langchain_mcp_adapters.client import MultiServerMCPClient, StreamableHttpConnection
from starter.agentic.state import UdaHubState, UserContext
from starter.agentic.nodes.validation import validation_node
from starter.agentic.nodes.enrichment import enrichment_node
from starter.agentic.nodes.supervisor import supervisor_node
from starter.agentic.nodes.memorization import memorization_node
from starter.agentic.nodes.chat_output import chat_output_node
from starter.agentic.chat_interface import ChatInterface, ConsoleChatInterface
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

import asyncio
import uuid

load_dotenv()


class UdaHubAgent:
    def _build_graph(self):
        graph = StateGraph(UdaHubState)

        # Define Nodes
        graph.add_node(
            node="validation",
            action=validation_node,
        )
        graph.add_node(
            node="enrichment",
            action=enrichment_node,
        )
        graph.add_node(
            node="supervisor",
            action=supervisor_node,
        )
        graph.add_node(node="memorize", action=memorization_node)
        graph.add_node(node="chat_output", action=chat_output_node)

        # Define Edges
        graph.add_edge(START, "validation")
        graph.add_conditional_edges(
            source="validation",
            path=self._after_validation,
            path_map={
                "enrich": "enrichment",
                "end": "chat_output",
            },
        )
        graph.add_edge("enrichment", "supervisor")
        graph.add_edge("supervisor", "memorize")
        graph.add_edge("memorize", "chat_output")
        graph.add_edge("chat_output", END)

        checkpointer = MemorySaver()
        return graph.compile(checkpointer=checkpointer)

    def _after_validation(self, state: UdaHubState) -> str:
        if state.get("task", {}).get("status") == "failed":
            return "end"
        return "enrich"

    def _build_mcp_client(self):
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
        self.graph = self._build_graph()
        self.mcp_client = self._build_mcp_client()
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
        chat_interface: ChatInterface = ConsoleChatInterface(),
    ):
        print("(You can quit the chat by sending an empty message)\n")
        print("Starting UDA Hub chat...")
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
                "chat_interface": chat_interface,
            },
        }

        print(f"Thread ID: {thread_id}\n")
        while True:
            # Invoke graph
            state = await self.graph.ainvoke(state, config=config)

            # End Chat if necessary
            if state.get("terminate_chat", False):
                break

            message = chat_interface.next_message()
            if not message:
                break

            # Add User Message
            state["messages"] = add_messages(state["messages"], [HumanMessage(message)])


if __name__ == "__main__":
    agent = UdaHubAgent()
    for i in range(1):
        asyncio.run(
            agent.start_chat(
                account_id="cultpass",
                exteranal_user_id="f556c0",
                thread_id="test_thread",
            )
        )
