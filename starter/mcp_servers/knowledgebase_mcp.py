from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session
from starter.data.models.cultpass import Experience
from starter.data.models.udahub import Knowledge
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import chromadb
import os

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_data")
CULTPASS_DB_PATH = os.getenv(
    "CULTPASS_DB_PATH", "sqlite:///starter/data/external/cultpass.db"
)
UDAHUB_DB_PATH = os.getenv("UDAHUB_DB_PATH", "sqlite:///starter/data/core/udahub.db")
KNOWLEDGE_BASE_MCP_PORT = int(os.getenv("KNOWLEDGE_BASE_MCP_PORT", "8002"))


def get_cultpass_experiences(database_url: str):
    engine = create_engine(database_url)
    with Session(engine) as session:
        stmt = select(Experience)
        experiences = session.execute(stmt).scalars().all()
        return experiences


def get_udahub_knowledge(database_url: str):
    engine = create_engine(database_url)
    with Session(engine) as session:
        stmt = select(Knowledge)
        entries = session.execute(stmt).scalars().all()
        return entries


mcp = FastMCP("UDA Hub Knowledgebase MCP Server")


@mcp.resource(
    uri="data://config",
    name="knowledgebase_config",
    description="Configuration for the knowledgebase.",
    mime_type="application/json",
    tags={"monitoring", "config"},
    meta={"author": "UDAHub Knowledge Base", "version": "1.0"},
)
def get_knowledgebase_config():
    return {
        "chroma_db_path": CHROMA_DB_PATH,
        "cultpass_db_path": CULTPASS_DB_PATH,
        "udahub_db_path": UDAHUB_DB_PATH,
    }


@mcp.tool(
    name="sync_cultpass_experiences",
    description="Synchronize the Cultpass experiences into the knowledgebase.",
    tags=set(["cultpass", "sync", "experiences"]),
    meta={"author": "UDAHub Knowledge Base", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def sync_cultpass_experiences():
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    experiences = get_cultpass_experiences(CULTPASS_DB_PATH)

    collection = chroma_client.get_or_create_collection(name="cultpass")

    for exp in experiences:
        collection.upsert(
            documents=[exp.description],
            metadatas=[
                {
                    "type": "experience",
                    "experience_id": exp.experience_id,
                    "title": exp.title,
                }
            ],
            ids=[f"experience_{exp.experience_id}"],
        )


@mcp.tool(
    name="sync_udahub_knowledgebase",
    description="Synchronize the UdaHub knowledge entries into the knowledgebase.",
    tags=set(["udahub", "sync"]),
    meta={"author": "UDAHub Knowledge Base", "version": "1.0"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def sync_udahub_knowledgebase():
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    knowledge_entries = get_udahub_knowledge(UDAHUB_DB_PATH)

    collection = chroma_client.get_or_create_collection(name="udahub")

    for entry in knowledge_entries:
        collection.upsert(
            documents=[entry.content],
            metadatas=[
                {
                    "type": "knowledge",
                    "title": entry.title,
                    "article_id": entry.article_id,
                    "account_id": entry.account_id,
                    "tags": entry.tags,
                }
            ],
            ids=[f"knowledge_{entry.article_id}"],
        )


class KnowledgeBaseEntry(BaseModel):
    collection: str = Field(description="The collection this entry belongs to")
    id: str = Field(
        description="The unique identifier for this knowledge entry in the collection"
    )
    title: str = Field(description="The title of the knowledge entry")
    content: str = Field(description="The content of the knowledge entry")


class UdaHubKnowledgeEntry(KnowledgeBaseEntry):
    article_id: str = Field(description="The unique identifier for the UdaHub article")
    account_id: str = Field(
        description="The account identifier associated with the UdaHub article"
    )


class KnowledgeBaseQuery(BaseModel):
    query_text: str = Field(description="The search query string")
    n_results: int = Field(
        default=5, description="The number of results to return from the query"
    )


class UdaHubKnowledgeBaseQuery(KnowledgeBaseQuery):
    account_id: str = Field(
        description="The ID of the UdaHub account to filter the knowledge entries by"
    )


@mcp.tool(
    name="query_udahub_knowledgebase",
    description="Query the UdaHub knowledgebase for learnings related to a given customer.",
    tags=set(["cultpass", "query", "knowledge"]),
    meta={"author": "UDAHub Knowledge Base", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def query_udahub_knowledgebase(query: UdaHubKnowledgeBaseQuery) -> list[dict] | dict:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_collection(name="udahub")
    query_result = collection.query(
        query_texts=[query.query_text],
        where={"acc": query.account_id},
        n_results=query.n_results,
    )

    result = []
    for i in range(len(query_result["ids"][0])):
        entry = UdaHubKnowledgeEntry(
            collection="udahub",
            id=query_result["ids"][0][i],
            title=query_result["metadatas"][0][i]["title"],
            content=query_result["documents"][0][i],
            article_id=query_result["metadatas"][0][i]["article_id"],
            account_id=query_result["metadatas"][0][i]["account_id"],
        )
        result.append(entry.model_dump())

    return result


class CultpassExperience(KnowledgeBaseEntry):
    experience_id: str = Field(
        description="The unique identifier for the Cultpass experience"
    )


@mcp.tool(
    name="query_cultpass_experiences",
    description="Query the Cultpass experiences knowledgebase.",
    tags=set(["cultpass", "query", "knowledge", "experiences"]),
    meta={"author": "UDAHub Knowledge Base", "version": "1.0"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def query_cultpass_experiences(query: KnowledgeBaseQuery) -> list[dict] | dict:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_collection(name="cultpass")
    query_result = collection.query(
        query_texts=[query.query_text],
        n_results=query.n_results,
    )

    result = []
    for i in range(len(query_result["ids"][0])):
        entry = CultpassExperience(
            collection="cultpass",
            id=query_result["ids"][0][i],
            title=query_result["metadatas"][0][i]["title"],
            content=query_result["documents"][0][i],
            experience_id=query_result["metadatas"][0][i]["experience_id"],
        )
        result.append(entry.model_dump())

    return result


if __name__ == "__main__":
    mcp.run(transport="http", port=KNOWLEDGE_BASE_MCP_PORT, log_level="debug")
