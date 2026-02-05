from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from langchain.agents import create_agent
from langchain.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field
from starter.agentic.state import Priority


class SupervisorAnalysis(BaseModel):
    agent: str = Field(
        "escalate_to_human", description="The agent that should handle the request."
    )
    priority: Priority = Field(
        "normal", description="The priority of the users request."
    )


async def supervisor_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    print("Calling superevisor")

    # Check termination
    if state.get("terminate_chat", False):
        return {"messages": [], "worker": "end"}

    # Check needs chat interaction
    if state.get("need_user_input", False) or state.get("has_pending_messages", False):
        return {"messages": [], "worker": "chat"}

    # configurable = config.get("configurable", {})
    # llm = configurable.get("llm")
    # available_agents = configurable.get("available_agents", [])
    # agents_list = "\n".join(
    #     [f"- {name}: {description}" for name, description in available_agents.items()]
    # )

    # agent = create_agent(
    #     model=llm,
    #     system_prompt=SystemMessage(f"""
    #     You are a supervisor agent inside a helpdesk chatbot.
    #     You need to analyze the user request and forward it to the most suitable worker agent, which will take over.
    #     These are the available worker agents:
    #     {agents_list}

    #     Additionally you also need to determine the priority of the request:
    #     - critical: Assign this for anything that is related to fraud or preventing harm from the user.
    #     - high: Assign this if the user is angry.
    #     - normal: Assign this as the default priority.

    #     Rules:
    #     - If the priority is critical alway assign "escalate_to_human" as the next agent.
    #     - If you cannot find a suitable agent assign "escalate_to_human".
    #     """),
    #     response_format=SupervisorAnalysis,
    # )
    # result = await agent.ainvoke(
    #     {"messages": state.get("messages", [])}, config={"recursion_limit": 5}
    # )
    # print(result)

    return {"messages": [], "worker": "escalate_to_human"}
