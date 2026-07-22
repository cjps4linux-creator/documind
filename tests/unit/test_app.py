from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from documind.app import app
from documind.db.models import Base
from documind.schemas import AskRequest
from documind.services.retrieval import RetrievalService
from documind.embeddings.adapter import EmbeddingAdapter
from documind.adapter.chat import ChatAdapter


class FakeEmbeddingAdapter(EmbeddingAdapter):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeChatAdapter(ChatAdapter):
    async def chat(self, messages):
        return "answer"


@pytest.fixture(autouse=True)
async def client():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.engine = engine
    app.state.embedder = FakeEmbeddingAdapter()
    app.state.chat_adapter = FakeChatAdapter()
    with TestClient(app) as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
