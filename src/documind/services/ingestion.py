from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable

from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncEngine

from documind.db.models import Chunk, ChunkEmbedding, Document, DocumentStatus
from documind.embeddings.adapter import EmbeddingAdapter
from documind.ingestion.chunker import chunk_text
from documind.schemas import IngestRequest, DocumentOut


class IngestService:
    def __init__(
        self,
        *,
        engine: AsyncEngine,
        embedder: EmbeddingAdapter,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> None:
        self.engine = engine
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def ingest(self, payload: IngestRequest) -> DocumentOut:
        document_id = str(uuid.uuid4())
        chunks = list(
            chunk_text(
                payload.text,
                chunk_size=payload.chunk_size or self.chunk_size,
                chunk_overlap=payload.chunk_overlap or self.chunk_overlap,
            )
        )
        chunks_text = [chunk.text for chunk in chunks]
        embeddings = await self.embedder.embed(chunks_text)
        embedding_dim = len(embeddings[0]) if embeddings else None
        metadata = {
            "embedding_provider": payload.embedding_provider.value,
            "chunk_size": payload.chunk_size or self.chunk_size,
            "chunk_overlap": payload.chunk_overlap or self.chunk_overlap,
            "chunk_count": len(chunks),
            **payload.metadata,
        }
        if embedding_dim is not None:
            metadata["embedding_dim"] = embedding_dim

        async with self.engine.connect() as conn:
            await conn.begin()
            try:
                await conn.execute(
                    insert(Document.__table__).values(
                        id=document_id,
                        title=payload.title,
                        status=DocumentStatus.ready.value,
                        doc_metadata=metadata,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )
                chunk_rows = [
                    {
                        "document_id": document_id,
                        "chunk_index": index,
                        "text": chunk.text,
                        "char_start": chunk.char_start,
                        "char_end": chunk.char_end,
                        "status": "indexed",
                        "created_at": datetime.utcnow(),
                    }
                    for index, chunk in enumerate(chunks)
                ]
                await conn.execute(insert(Chunk.__table__).values(chunk_rows))
                result = await conn.execute(select(Chunk.id).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index))
                db_chunk_ids = [row[0] for row in result.fetchall()]
                embedding_rows = [
                    {"chunk_id": db_chunk_ids[index], "embedding": embeddings[index]}
                    for index in range(len(db_chunk_ids))
                ]
                await conn.execute(insert(ChunkEmbedding.__table__).values(embedding_rows))
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

        return DocumentOut(
            id=document_id,
            title=payload.title,
            status=DocumentStatus.ready.value,
            metadata=metadata,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

    async def delete_document(self, document_id: str) -> None:
        async with self.engine.connect() as conn:
            await conn.begin()
            try:
                chunk_ids = (
                    await conn.execute(select(Chunk.id).where(Chunk.document_id == document_id))
                ).scalars().all()
                if chunk_ids:
                    await conn.execute(
                        delete(ChunkEmbedding.__table__).where(ChunkEmbedding.chunk_id.in_(chunk_ids))
                    )
                await conn.execute(delete(Chunk.__table__).where(Chunk.document_id == document_id))
                await conn.execute(delete(Document.__table__).where(Document.id == document_id))
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
