# Agentic Graph

``` mermaid
---
config:
    theme: dark
    flowchart:
        curve: linear
---

graph LR;

    __start__([<p>__start__</p>]):::first

    subgraph Validation
        direction LR

        Validation__create_udahub_user{{UDAHub_MCP::create_udahub_user}}:::tool
        Validation__find_udahub_user{{UDAHub_MCP::find_udahub_user}}:::tool
        Validation__get_cultpass_user{{Cultpass_MCP::get_cultpass_user}}:::tool
    end

    subgraph Enrichment
        direction LR    
    end

    subgraph Supervisor
        direction LR
    end

    subgraph Read_Message
        direction LR
    end

    subgraph Send_Message
        direction LR    
    end

    subgraph Reservation
        direction LR

        Reservation__get_cultpass_reservations{{Cultpass_MCP::get_cultpass_reservations}}:::tool
        Reservation__cancel_cultpass_reservation{{Cultpass_MCP::cancel_cultpass_reservation}}:::tool
        Reservation__make_cultpass_reservation{{Cultpass_MCP::make_cultpass_reservation}}:::tool
    end

    subgraph Subscription
        direction LR

        Subscription__get_cultpass_user{{UDAHub_MCP::get_cultpass_user}}:::tool
        Subscription__cancel_cultpass_subscription{{UDAHub_MCP::cancel_cultpass_subscription}}:::tool
        Subscription__reactivate_cultpass_subscription{{UDAHub_MCP::reactivate_cultpass_subscription}}:::tool
        Subscription__upgrade_cultpass_subscription{{UDAHub_MCP::upgrade_cultpass_subscription}}:::tool
    end

    subgraph Browsing
        direction LR

        Browsing__query_cultpass_experiences{{UDAHub_MCP::query_cultpass_experiences}}:::tool
        Browsing__get_cultpass_experience{{Cultpass_MCP::get_cultpass_experience}}:::tool
    end

    subgraph FAQ
        direction LR

        FAQ__query_udahub_knowledgebase{{UDAHub_MCP::query_udahub_knowledgebase}}:::tool
    end

    subgraph Escalate_to_Human
        direction LR
    end

    subgraph Memorization
        direction LR

        Memorization__sync_cultpass_experiences{{Knowledgebase_MCP::sync_cultpass_experiences}}:::tool
        Memorization__sync_udahub_knowledgebase{{Knowledgebase_MCP::sync_udahub_knowledgebase}}:::tool
    end

    subgraph Legend
        direction TB

        Legend__system_agent[System Agent]
        Legend__worker_agent[Worker Agent]:::worker_agent
        Legend__tool{{Tool}}:::tool
    end

    
    __end__([<p>__end__</p>]):::last

    __start__ --> Validation;
    Validation --> Enrichment;
    Enrichment --> Supervisor;

    Supervisor -.-> Read_Message;
    Read_Message --> Supervisor;

    Supervisor -.-> Send_Message;
    Send_Message --> Supervisor;

    Supervisor -.-> Reservation;
    Reservation --> Supervisor;

    Supervisor -.-> Subscription;
    Subscription --> Supervisor;

    Supervisor -.-> Browsing;
    Browsing --> Supervisor;

    Supervisor -.-> FAQ;
    FAQ --> Supervisor;

    Supervisor -.-> Escalate_to_Human;
    Escalate_to_Human --> Supervisor;

    Supervisor --> Memorization;    
    Memorization --> __end__

classDef tool font-size:90%,line-height:1,stroke:#ffae0c,stroke-width:2px,color:#ffae0c;

classDef worker_agent stroke:#02b3e4,stroke-width:2px,color:#02b3e4;
class Reservation,Subscription,FAQ,Browsing,Escalate_to_Human worker_agent;

%%	classDef default fill:#f2f0ff,line-height:1.2
%%	classDef first fill-opacity:0
%%	classDef last fill:#bfb6fc

```

## System Agents

The system agents form the framework of the conversation and orchestrate the flow between different worker agents and tools.

### `validation`

Ensures that the requested account is a valid customer of UDA-Hub and also validates the user's identity with the customer's system.
It also ensures that there is a corresponding user account in the UDA Hub database, creating one if necessary.

### `enrichment`

TODO

### `supervisor`

The central orchestrator that decides what should happen next.
It analyzes the current conversation state and routes control to the most suitable worker agent (or to messaging/escalation) and then regains control once that step is done.

### `read_message`

Asks the user for input when needed and captures their response to be processed by the Supervisor agent and subsequent worked agents.

### `send_message`

Delivers pending agent responses to the chat interface.
It is used whenever the system has something to communicate back to the user and ensures messages are emitted in a consistent way.

### `memorize`

TODO



## Worker Agents

The following worker agents are available in UDA-Hub and can be used to enables complex, real-world agentic workflows.
The Supervisor agent decides (based on the conversation context) which worker agent should take the next step.
Each worker agent has a clearly scoped set of tools and a dedicated focus.
The customer decides which worker agents are plugged in for use based on their needs, and the Supervisor agent ensures that the right one is engaged at the right time.

### `faq`

Answers common questions based on the knowledge base.
This agent primarily uses read-only knowledge tools and asks follow-up questions when context is missing instead of making assumptions.

### `reservation`

Handles everything related to reservations (e.g., viewing, creating, canceling, changing).
Before executing any action that changes state, the agent asks the user for explicit confirmation.

### `subscription`

Works on subscription-related topics (e.g., checking status, canceling, reactivating, upgrading).
As with reservations, state-changing actions are only executed after clear user confirmation.

### `browsing`

Helps users browse a customer's offerings/experiences: search, details, comparisons, and recommendations.
The agent can inform and provide context, but it does not perform bookings/reservations itself (that is handled by, e.g., `reservation`).

### `escalate_to_human`

Fallback agent for cases where the request is outside the available tool capabilities or when a human should take over.
It terminates the chat flow and signals a handoff to a human agent.

