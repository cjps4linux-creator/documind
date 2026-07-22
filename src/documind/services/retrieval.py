from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from documind.adapter.chat import ChatAdapter
from documind.db.engine import engine
from documind.embeddings.adapter import EmbeddingAdapter
from documind.schemas import AskRequest, AskResponse, Citation


class RetrievalService:
    def __init__(self, *, engine: AsyncEngine, embedder: EmbeddingAdapter, chat_adapter: ChatAdapter) -> None:
        self.engine = engine
        self.embedder = embedder
        self.chat_adapter = chat_adapter

    async def ask(self, payload: AskRequest) -> AskResponse:
        query_embedding = (await self.embedder.embed([payload.query]))[0]
        stmt = text(
            """
            SELECT c.id, c.document_id, c.text, d.title, 1 - (e.embedding <=> CAST(:query AS vector)) AS score
            FROM chunk_embeddings e
            JOIN chunks c ON c.id = e.chunk_id
            LEFT JOIN documents d ON d.id = c.document_id
            WHERE 1 - (e.embedding <=> CAST(:query AS vector)) >= :min_score
            ORDER BY score DESC
            LIMIT :top_k
            """
        ).bindparams(query=str(query_embedding), min_score=payload.min_score, top_k=payload.top_k)
        async with self.engine.connect() as conn:
            rows = (await conn.execute(stmt)).mappings().all()
        context_rows = "\n".join([f"- {row['text']}" for row in rows])
        prompt = (
            "Answer the user question from the retrieved context. Cite sources inline using [chunk_id:score] markers, for example [47:0.83]. Do not cite outside the context.\n\n"
            f"Context:\n{context_rows}\n\nQuestion: {payload.query}"
        )
        answer = await self.chat_adapter.chat(messages=[{"role": "system", "content": "Return concise markdown answer with inline chunk citations like [47:0.83]."}, {"role": "user", "content": prompt}])
        citations = [Citation(chunk_id=row["id"], document_id=row["document_id"], title=row["title"], text=row["text"], score=float(row["score"])) for row in rows]
        return AskResponse(query=payload.query, answer=answer, citations=citations, provider=payload.provider, retrieved_chunks=len(rows))
