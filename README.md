#### ND901 - Agentic AI Engineer with LangChain and LangGraph

# Project 3: Autonomous Knowledge Agent

UDA-Hub, a Universal Decision Agent, is an a Help Desk assistant driven by agentic AI. 
It is designed to plug into existing systems and help the users of those systems with their help desk requests.
UDA-Hub achieves this by accessing both UDA-Hub's internal knowledgebase and external tools that connect to the systems used by the customers.
A wide range of predefined worker agents is provided by UDA-Hub, but each customer can define which agents are plugged into their instance of UDA-Hub, defining what the agent is capable of doing for their users.

### Showcase: Cultpass Card

In this project the concept is demonstrated with a fictional travel experience company called Cultpass Card, which offers various travel experiences to its customers.
Users holding a subscription to the Cultpass Card can book these experiences. Cultpass offers two subscription tiers: Standard and Premium. Premium allows the holder to book more exclusive experiences with less availability, while Standard offers a more limited selection.
Typical user requests are related to checking, modifying, or cancelling reservations, changing, continuing or cancelling subscriptions, and asking for recommendations on which experience to book next based on the user's preferences and past bookings.
Of course there are also more general FAQ-type questions that users might have, which can be answered by the agent as well.

### Architecture

UDA-Hub provisions an architecture that allows customers to plug into UDA-Hub and delegate help desk requests to the agent, which can then use the tools provided by the customer to perform the necessary actions to resolve the user's request.

![alt text](images/architecture.svg)


### Short-term Memory

The UDA-Hub Chat Agent utilizes an in-memory checkpointing mechanism. That means as long as the session has not been terminated, it allows any user to continue a conversation without losing context even after terminating the chat.
This also allows faster response times as the agent does not need to go through the overhead of validating the user and retrieving context from long-term memory on every single request.

### Long-term Memory

Additionally, UDA-Hub also stores the conversation history in a persistent store encapsulated in tickets. 
Using the ticket ID, a user can continue long-running conversations even after the in-memory checkpoint has been terminated.

### Learning and Knowledge Growth

Upon completion of a ticket UDA-Hub also tries to extract new learnings from the conversation and stores these in a knowledgebase.
This allows the agent to grow its knowledge over time and provide better answers to the users.

## Prerequisites

This project is set up on top of the python tooling of [Astral.sh](https://astral.sh/), escpecially their package manager `uv`. If you have it already installed you can set up this project and install all dependencies by running the following command inside the root folder.

```bash
uv sync
``` 

Make sure to validate that the virtual environment is activated after installing the dependencies. 
If it's not activated, you can activate it with the following command:

```bash
source .venv/bin/activate
```

## Running UDA-Hub

In order to run UDA-Hub, you need to start the MCP servers (see [MCP Servers](#mcp-servers)) first so that the agtents have access to all the necessary tools.
Run each of these commands in separate terminal windows to maintain visibility on the logs of each server:

```bash
python -m starter.mcp_servers.udahub_mcp
python -m starter.mcp_servers.knowledgebase_mcp
python -m starter.mcp_servers.cultpass_mcp
```

Alternatively, you can run all MCP servers in the background with the following commands and then use `wait` to keep the terminal open:

```bash
python -m starter.mcp_servers.udahub_mcp & 
python -m starter.mcp_servers.knowledgebase_mcp & 
python -m starter.mcp_servers.cultpass_mcp &

wait
```



## Showcase



## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `OPENAI_API_KEY` | (required) | API key used by `langchain_openai.ChatOpenAI` (required to run the agent). |
| `UDAHUB_DB_PATH` | `sqlite:///starter/data/core/udahub.db` | SQLAlchemy connection string for the UDA Hub core database (used by the UDA Hub MCP server and DB helpers). |
| `CULTPASS_DB_PATH` | `sqlite:///starter/data/external/cultpass.db` | SQLAlchemy connection string for the Cultpass external database (used by the Cultpass MCP server and knowledgebase sync). |
| `CHROMA_DB_PATH` | `./chroma_data` | Filesystem path for the persistent ChromaDB store (used by the knowledgebase MCP server). |
| `UDAHUB_MCP_PORT` | `8001` | Port for the UDA Hub MCP server HTTP transport. |
| `KNOWLEDGE_BASE_MCP_PORT` | `8002` | Port for the Knowledgebase MCP server HTTP transport. |
| `CULTPASS_MCP_PORT` | `8003` | Port for the Cultpass MCP server HTTP transport. |

## Tracing

This project supports request/response tracing via **LangSmith**. If you set the environment variables below, LangChain/LangGraph will emit traces that you can inspect in the LangSmith UI.

| Variable | Default | Description |
| --- | --- | --- |
| `LANGSMITH_TRACING` | (unset / `false`) | Enable or disable tracing (set to `true` to turn tracing on). |
| `LANGSMITH_API_KEY` | (required for tracing) | LangSmith API key used to authenticate trace uploads. |
| `LANGSMITH_ENDPOINT` | (LangSmith default) | Optional custom endpoint (useful for EU region or self-hosted LangSmith). |
| `LANGSMITH_PROJECT` | (LangSmith default) | Optional project name to group traces (e.g. `Development`). |
