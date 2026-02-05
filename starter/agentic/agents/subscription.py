from starter.agentic.state import UdaHubState
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage
from langchain.agents import create_agent
from starter.agentic.mcp_tool_utils import McpToolFilter
from starter.agentic.agents.agent_response import AgentResponse
from textwrap import dedent


async def subscription_agent_node(
    state: UdaHubState, config: RunnableConfig
) -> UdaHubState:
    tools = config.get("configurable", {}).get("mcp_tools", [])
    llm = config.get("configurable", {}).get("llm")
    user = state.get("user", {})
    external_user_id = user.get("external_user_id", "")
    account_id = user.get("account_id", "")
    account_name = user.get("account_name", account_id)
    account_description = user.get("account_description", "")

    subscription_tools = (
        McpToolFilter(tools).by_tags(["subscription", account_id]).get_all()
    )
    system_prompt = dedent(f"""
        You are an agent that helps users manage their subscriptions for {account_name} (account_id={account_id}).
        {account_description}
        
        Your task is to assist users with managing their subscriptions (e.g. canelling, changing, renewing, etc.). 
        You have access to tools that allow you to manage the users subscriptions.

        Rules:
        - Use the tools instead of the LLMs knowledge to answer questions.
        - If you need more information from the user, ask the user for it instead of making assumptions.
        - If you cannot find what the users looking for, say that you are sorry and that you cannot help with this request.
        - If the user askes to do something that is outside of your capabilities, set the 'request_handoff' flag to true in your response.
        - Always ask the user if the request is complete or if they need further assistance. Only if they confirm that they are done, set the 'task_complete' flag to true in your response.
        - Before you perform any action that changes the users subscription, always ask the user for confirmation. Only after they confirm, perform the action.

        User ID in the customers system: {external_user_id}
    """)
    agent = create_agent(
        model=llm,
        system_prompt=SystemMessage(system_prompt),
        tools=subscription_tools,
        response_format=AgentResponse,
    )
    response = await agent.ainvoke(
        {"messages": state.get("messages", [])}, config={"recursion_limit": 10}
    )
    structured_response: AgentResponse = response["structured_response"]
    return {
        "messages": [AIMessage(content=structured_response.ai_response)],
        "has_pending_messages": True,
        "need_user_input": structured_response.user_follow_up_needed,
        "handoff_requested": structured_response.request_handoff,
        "terminate_chat": structured_response.task_complete,
    }
