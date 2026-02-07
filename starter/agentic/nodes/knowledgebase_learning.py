from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState
from starter.agentic.mcp_tool_utils import McpToolFilter
from starter.data.udahub_db import create_knowledge_entry
from langchain.agents import create_agent
from pydantic import BaseModel, Field
from textwrap import dedent


class KnowledgeExtractionResult(BaseModel):
    new_knowledge: bool = Field(
        description="A tag indicating whether new knowledge was extracted from the conversation that should be added to the knowledge base."
    )
    title: str = Field(
        description="A short title for the knowledge in form of a question, e.g. 'How to reset password?'."
    )
    content: str = Field(
        description="The detailed content or answer corresponding to the title/question."
    )
    tags: str = Field(
        description="A comma-separated list of tags or keywords related to the knowledge."
    )


async def knowledgebase_learning_node(
    state: UdaHubState, config: RunnableConfig
) -> UdaHubState:
    user = state.get("user", {})
    account_id = user.get("account_id", "")
    llm = config.get("configurable", {}).get("llm")

    messages = state.get("messages", [])
    conversation = "\n================================================\n".join(
        [f"{message.type}: {message.content}" for message in messages]
    )

    tools = config.get("configurable", {}).get("mcp_tools", [])
    learning_tools = (
        McpToolFilter(tools)
        .by_author("UDAHub Knowledge Base")
        .by_tags(["learning"])
        .get_all()
    )

    agent = create_agent(
        model=llm,  # ty:ignore[invalid-argument-type]
        system_prompt=dedent(f"""
        You are a helpful assistant for extracting knowledge from conversations between customers and support agents.
        Your task is to analyze the conversation and determine if there is any new knowledge that can be extracted and added to the knowledge base.
        The knowledge should be useful for answering future questions from customers and should not be too specific to the current conversation.

        Plan:
        1. Analyze the conversation and identify if there are any general questions that were answered by the support agent.
        2. Reflect whether this knowledge is really relevant for future customers or if it is too specific to the current conversation.
        3. If you determine that this is the case, check with the existing knowledgebase if it already contains this knowledge. If it does, then there is no need to add it again.
        4. If you determine that this is new and relevant knowledge, then create a short title for the knowledge in form of a question (e.g. 'How to reset password?')
        and a detailed content or answer corresponding to the title/question. Also provide some tags or keywords related to the knowledge.

        Rules:
        - Be concise and to the point. The title should not be more than 10 words and the content should not be more than 100 words.
        - Only extract knowledge that is relevant for future customers and not too specific to the current conversation.
        - If the conversation does not contain any new and relevant knowledge, then indicate that as well.
        - If you find somehing similar in the knowledge base that either explicitly or implicitly contains the same knowledge, then there is no need to add it again.
        - Do not create knowledge base entries covering products of the customer company as these are likely to change frequently and the knowledge base should contain evergreen content that is not changing too much over time.
        - Be mindful not to spam the knowledge base with redundant or low-quality entries. Only add knowledge that is truly valuable and enhances the overall quality of the knowledge base.
        
        Conversation:
        {conversation}
        """),
        response_format=KnowledgeExtractionResult,
        tools=learning_tools,
    )
    response = await agent.ainvoke({}, config={"recursion_limit": 10})
    analysis_result: KnowledgeExtractionResult = response["structured_response"]

    if analysis_result.new_knowledge:
        print(analysis_result)
        create_knowledge_entry(
            account_id=account_id,
            title=analysis_result.title,
            content=analysis_result.content,
            tags=analysis_result.tags,
        )

    return state
