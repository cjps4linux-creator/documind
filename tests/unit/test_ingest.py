from __future__ import annotations

from datetime import datetime
from typing import Iterable
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from documind.db.models import Base, Chunk, Document, DocumentStatus, ChunkStatus
from documind.schemas import IngestRequest
from documind.services.ingestion import IngestService
from documind.embeddings.adapter import EmbeddingAdapter


class FakeEmbeddingAdapter(EmbeddingAdapter):
    async def embed(self, texts: Iterable[str]) -> list[list[float]]:
        return [[0.1] * 6 for _ in texts]


@pytest.fixture
async def sqlite_engine():
    engine = create_async_engine("sqlite+aiosqlite://")
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_ingest_splits_chunks_and_embeds(sqlite_engine):
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    service = IngestService(engine=sqlite_engine, embedder=FakeEmbeddingAdapter(), chunk_size=8, chunk_overlap=2)
    payload = IngestRequest(title="t", text="0123456789abcdef")
    document = await service.ingest(payload)
    assert document.status == DocumentStatus.ready.value
    assert document.metadata["chunk_count"] >= 1
    assert document.metadata["embedding_dim"] == 6


@pytest.mark.asyncio
async def test_delete_document_removes_data(sqlite_engine):
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    service = IngestService(engine=sqlite_engine, embedder=FakeEmbeddingAdapter(), chunk_size=8, chunk_overlap=2)
    payload = IngestRequest(title="t", text="0123456789abcdef")
    document = await service.ingest(payload)
    await service.delete_document(document.id)
    from sqlalchemy import select
    async with sqlite_engine.connect() as conn:
        result = await conn.execute(select(Document).where(Document.id == document.id))
        assert result.scalar_one_or_none() is None
