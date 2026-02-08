from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from starter.agentic.state import Priority
from textwrap import dedent


class SupervisorAnalysis(BaseModel):
    agent: str = Field(
        "escalate_to_human", description="The agent that should handle the request."
    )
    priority: Priority = Field(
        "normal", description="The priority of the users request."
    )


async def supervisor_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    # Check for pending messages
    if state.get("has_pending_messages", False):
        return {"messages": [], "worker": "send_message"}

    # Check termination
    if state.get("terminate_chat", False):
        return {"messages": [], "worker": "end"}

    # Check if user input is needed
    if state.get("need_user_input", False):
        return {"messages": [], "worker": "read_message"}

    user = state.get("user", {})
    account_id = user.get("account_id", "")
    account_name = user.get("account_name", account_id)
    account_description = user.get("account_description", "")

    configurable = config.get("configurable", {})
    llm = configurable.get("llm")
    available_agents = configurable.get("available_agents", [])
    agents_list = "\n".join(
        [f"- {name}: {description}" for name, description in available_agents.items()]
    )

    agent = create_agent(
        model=llm,  # ty:ignore[invalid-argument-type]
        system_prompt=SystemMessage(
            dedent(f"""
        You are a supervisor agent inside a helpdesk chatbot for {account_name} (account_id={account_id}):
        {account_description}

        You need to analyze the user request and forward it to the most suitable worker agent, which will take over.
        These are the available worker agents:
        {agents_list}

        Additionally you also need to determine the priority of the request:
        - critical: Assign this for anything that is related to fraud or preventing harm from the user.
        - high: Assign this if the user is angry.
        - normal: Assign this as the default priority.

        Rules:
        - If the priority is critical always assign "escalate_to_human" as the next agent.
        - If you cannot find a suitable agent assign "escalate_to_human".
        """)
        ),
        response_format=SupervisorAnalysis,
    )
    result = await agent.ainvoke(
        {"messages": state.get("messages", [])}, config={"recursion_limit": 5}
    )
    response: SupervisorAnalysis = result["structured_response"]

    return {
        "messages": [],
        "worker": response.agent,
        "priority": response.priority,
    }
