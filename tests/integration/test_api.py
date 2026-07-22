from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from documind.app import app
from documind.db.models import Base, Chunk, ChunkEmbedding, Document, DocumentStatus
from documind.services.ingestion import IngestService
from documind.embeddings.adapter import EmbeddingAdapter
from documind.adapter.chat import ChatAdapter


class FakeEmbeddingAdapter(EmbeddingAdapter):
    async def embed(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeChatAdapter(ChatAdapter):
    async def chat(self, messages):
        return "answer"


@pytest.fixture()
def sqlite_engine():
    engine = create_async_engine("sqlite+aiosqlite://")
    return engine


@pytest.fixture()
async def db_engine(sqlite_engine):
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield sqlite_engine
    await sqlite_engine.dispose()


@pytest.fixture()
def app_with_state(db_engine):
    app.state.engine = db_engine
    app.state.embedder = FakeEmbeddingAdapter()
    app.state.chat_adapter = FakeChatAdapter()
    return app


def test_health(app_with_state):
    with TestClient(app_with_state) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_returns_document(app_with_state):
    with TestClient(app_with_state) as client:
        response = client.post("/ingest", json={"text": "DocuMind is an AI document intelligence platform."})
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "ready"
    assert data["metadata"]["chunk_count"] >= 1


def test_ask_returns_answer(app_with_state):
    from documind.config import settings
    if "postgres" not in settings.DATABASE_URL:
        pytest.skip("retrieval requires postgres/pgvector")
    with TestClient(app_with_state) as client:
        client.post("/ingest", json={"text": "DocuMind is an AI document intelligence platform."})
        response = client.post("/ask", json={"query": "What is DocuMind?", "top_k": 2})
    assert response.status_code == 200
    assert response.json()["answer"] == "answer"
    assert response.json()["retrieved_chunks"] >= 0
