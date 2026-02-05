from langchain_core.runnables import RunnableConfig
from starter.agentic.state import UdaHubState


async def enrichment_node(state: UdaHubState, config: RunnableConfig) -> UdaHubState:
    if state.get("is_enriched", False) is True:
        return state

    # TODO: implement
    ticket_id = state.get("ticket_id", None)
    if ticket_id:
        pass

    return {"messages": [], "is_enriched": True}
