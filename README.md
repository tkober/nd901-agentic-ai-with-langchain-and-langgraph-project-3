#### ND901 - Agentic AI Engineer with LangChain and LangGraph

# Project 3: Autonomous Knowledge Agent



## Prerequisites

This project is set up on top of the python tooling of [Astral.sh](https://astral.sh/), escpecially their package manager `uv`. If you have it already installed you can set up this project and install all dependencies by running the following command inside the root folder.

```bash
uv sync
``` 

## MCP Servers

### UDA Hub MCP Server

| Name | Type | Description | Arguments | Tags | ReadOnly | Destructive | Idempotent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `create_udahub_user` | tool | Create a new user in the UdaHub database. | `account_id: str`, `external_user_id: str`, `user_name: str` | `udahub`, `user`, `create`, `validation` | no | no | no |
| `get_udahub_user` | tool | Retrieve user details from the UdaHub database by using the internal UDA Hub user ID. | `user_id: str` | `udahub`, `user`, `details` | yes | no | yes |
| `find_udahub_user` | tool | Find a user in the UdaHub database by using the account ID of a customer and the external user ID. | `account_id: str`, `external_user_id: str` | `udahub`, `user`, `details`, `validation` | yes | no | yes |
| `get_udahub_account` | tool | Retrieve account details from the UdaHub database. | `account_id: str` | `udahub`, `account`, `details` | yes | no | yes |

### UDA Hub Knowledgebase MCP Server

| Name | Type | Description | Arguments | Tags | ReadOnly | Destructive | Idempotent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `knowledgebase_config` | resource (`data://config`) | Configuration for the knowledgebase. | - | `monitoring`, `config` | - | - | - |
| `sync_cultpass_experiences` | tool | Synchronize the Cultpass experiences into the knowledgebase. | - | `cultpass`, `sync`, `experiences` | no | no | yes |
| `sync_udahub_knowledgebase` | tool | Synchronize the UdaHub knowledge entries into the knowledgebase. | - | `udahub`, `sync` | no | no | yes |
| `query_udahub_knowledgebase` | tool | Query the UdaHub knowledgebase for learnings related to a given customer. | `account_id: str`, `query_text: str`, `n_results: int (0..10)` | `cultpass`, `query`, `knowledge`, `faq` | yes | no | yes |
| `query_cultpass_experiences` | tool | Query the experiences which Cultpass offers. | `query_text: str`, `n_results: int (0..10)` | `cultpass`, `query`, `knowledge`, `experiences`, `browsing` | yes | no | yes |

### Cultpass MCP Server

| Name | Type | Description | Arguments | Tags | ReadOnly | Destructive | Idempotent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `get_cultpass_user` | tool | Retrieve user details from the Cultpass database. | `user_id: str` | `cultpass`, `user`, `details`, `subscription`, `validation` | yes | no | yes |
| `cancel_cultpass_subscription` | tool | Cancel a user's subscription in the Cultpass database. | `user_id: str` | `cultpass`, `subscription`, `cancel` | no | yes | no |
| `reactivate_cultpass_subscription` | tool | Reactivate a user's cancelled subscription in the Cultpass database. | `user_id: str` | `cultpass`, `subscription`, `reactivate` | no | no | no |
| `upgrade_cultpass_subscription` | tool | Upgrade a user's subscription to premium in the Cultpass database. | `user_id: str` | `cultpass`, `subscription`, `upgrade` | no | no | no |
| `get_cultpass_reservations` | tool | Retrieve reservations for a user from the Cultpass database. | `user_id: str` | `cultpass`, `reservation`, `details` | yes | no | yes |
| `cancel_cultpass_reservation` | tool | Cancel a reservation for a user in the Cultpass database. | `user_id: str`, `reservation_id: str` | `cultpass`, `reservation`, `cancel` | no | yes | no |
| `make_cultpass_reservation` | tool | Make a reservation for a user in the Cultpass database. | `user_id: str`, `experience_id: str` | `cultpass`, `reservation`, `create` | no | no | no |
| `get_cultpass_experience` | tool | Retrieve experience details from the Cultpass database. | `experience_id: str` | `cultpass`, `experience`, `details`, `browsing` | yes | no | yes |



## Agents


``` mermaid
---
config:
    theme: dark
    flowchart:
        curve: linear
---

graph TD;

	__start__([<p>__start__</p>]):::first
    
    subgraph Validation
        direction TB

        subgraph UserRetrival[User Retrieval]
            direction LR
            retrieve_user_details{{retrieve_user_details}}:::tool
            retrieve_subscription{{retrieve_subscription}}:::tool
        end

        ValidateUser[User Validation]

        Validation__in([in]) --> UserRetrival;
        UserRetrival --> ValidateUser;
        ValidateUser --> Validation__out([out])
    
    end

    subgraph Enrichment
        direction TB
        
        Enrichment__in([in])
        Sentiment[Sentiment Analysis]
        Urgency
        subgraph Metadata
            direction LR
            retrieve_ticket_messages{{retrieve_ticket_messages}}:::tool
            retrieve_ticket_metadata{{retrieve_ticket_metadata}}:::tool
        end
        Enrichment__out([out])

        Enrichment__in --> Sentiment;
        Enrichment__in --> Urgency;
        Enrichment__in --> Metadata;

        Sentiment --> Enrichment__out;
        Urgency --> Enrichment__out;
        Metadata --> Enrichment__out;

    end
    
    subgraph Supervisor
        direction TB

        Supervisor__in([in])
        Esclation[Escalate to Human]
        
        subgraph Reservation
            direction TB

            Reservation__in([in])
            CheckAvailability[Check Availability]
            ConfirmReservation[Confirm Reservation]
            MakeReservation[Book Reservation]
            Reservation__out([out])

            Reservation__in --> CheckAvailability;
            CheckAvailability -.-> Reservation__out;
            CheckAvailability -.-> ConfirmReservation;
            ConfirmReservation -.-> MakeReservation;
            ConfirmReservation -.-> Reservation__out;
            MakeReservation --> Reservation__out;
        end

        subgraph CancelReservation[Cancel Reservation]
            direction TB

            CancelReservation__in([in])
            CancelReservation__CheckReservation[Check Reservation]
            CancelReservation__ConfirmCancelation[Confirm Cancelation]
            CancelReservation__PerformCancelation[Perform Cancelation]
            CancelReservation__out([out])

            CancelReservation__in --> CancelReservation__CheckReservation;
            CancelReservation__CheckReservation -.-> CancelReservation__out;
            CancelReservation__CheckReservation -.-> CancelReservation__ConfirmCancelation;
            CancelReservation__ConfirmCancelation -.-> CancelReservation__out;
            CancelReservation__ConfirmCancelation -.-> CancelReservation__PerformCancelation;
            CancelReservation__PerformCancelation --> CancelReservation__out;
        end


        subgraph CancelSubscription[Cancel Subscription]
            direction TB

            CancelSubscription__in([in])
            CancelSubscription__CheckSubscription[Check Subscription]
            CancelSubscription__ConfirmCancelation[Confirm Cancelation]
            CancelSubscription__PerformCancelation[Perform Cancelation]
            CancelSubscription__out([out])

            CancelSubscription__in --> CancelSubscription__CheckSubscription;
            CancelSubscription__CheckSubscription -.-> CancelSubscription__out;
            CancelSubscription__CheckSubscription -.-> CancelSubscription__ConfirmCancelation;
            CancelSubscription__ConfirmCancelation -.-> CancelSubscription__out;
            CancelSubscription__ConfirmCancelation -.-> CancelSubscription__PerformCancelation;
            CancelSubscription__PerformCancelation --> CancelSubscription__out;
        end
            
        
        subgraph Browsing
            direction LR
            retrieve_experiences{{retrieve_experiences}}:::tool
        end
        
   
        
        subgraph HelpDesk[Help Desk]
            direction LR
            retrieve_knowledge{{retrieve_knowledge}}:::tool
        end
        
        Supervisor__out([out])


        Supervisor__in -.-> Supervisor__out;
        Supervisor__in -.-> Esclation;
        Supervisor__in -.-> Reservation;
        Supervisor__in -.-> CancelReservation;
        Supervisor__in -.-> Browsing;
        Supervisor__in -.-> CancelSubscription;
        Supervisor__in -.-> HelpDesk;

        Esclation --> Supervisor__in;
        Reservation --> Supervisor__in;
        CancelReservation --> Supervisor__in;
        Browsing --> Supervisor__in;
        CancelSubscription --> Supervisor__in;
        HelpDesk --> Supervisor__in;


    end

    subgraph Memomrize
        direction TB
        Memomrize__in([in])
        Memomrize__in --> Summarize[Summarize Ticket];
        Summarize --> UpsertTicket["Upsert Ticket (Messages, Metadata, ...)"];
        UpsertTicket --> StoreKnowledge[Store Knowledge];
        StoreKnowledge --> Memomrize__out; 
        Memomrize__out([out])
    end
	
    __end__([<p>__end__</p>]):::last
	
	
    __start__ --> Validation;
    
    Validation -.-> Enrichment;
    Validation -.-> __end__;
    Validation -.-> Supervisor;
    Enrichment --> Supervisor;
	Supervisor --> Memomrize;
    Memomrize --> __end__;

classDef tool font-size:90%,line-height:1;

%%	classDef default fill:#f2f0ff,line-height:1.2
%%	classDef first fill-opacity:0
%%	classDef last fill:#bfb6fc

```