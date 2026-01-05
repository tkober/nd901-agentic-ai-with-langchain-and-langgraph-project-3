#### ND901 - Agentic AI Engineer with LangChain and LangGraph

# Project 3: Autonomous Knowledge Agent


## Prerequisites

This project is set up on top of the python tooling of [Astral.sh](https://astral.sh/), escpecially their package manager `uv`. If you have it already installed you can set up this project and install all dependencies by running the following command inside the root folder.

```
uv sync
``` 


``` mermaid
---
config:
  flowchart:
    curve: linear
---

graph TD;

	__start__([<p>__start__</p>]):::first
    
    subgraph Validation
        direction TB

        UserRetrival --> ValidateUser;
    
    end

    subgraph Enrichment
        direction TB
        
        in([in])
        Sentiment
        Urgency
        out([out])

        in --> Sentiment;
        in --> Urgency;

        Sentiment --> out;
        Urgency --> out;

    end
    
    subgraph Supervisor
        direction TB
    end

    subgraph Memomrize
        direction TB
    end
	
    __end__([<p>__end__</p>]):::last
	
	
    __start__ --> Validation;
    
    Validation -.-> Enrichment;
    Validation -.-> __end__;
    Enrichment --> Supervisor;
	Supervisor --> Memomrize;
    Memomrize --> __end__;

	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```