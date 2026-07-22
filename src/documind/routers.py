from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, insert, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from documind.db.models import Chunk, ChunkEmbedding, Document, DocumentStatus
from documind.schemas import (
    AskRequest,
    AskResponse,
    Citation,
    DocumentOut,
    IngestRequest,
    Provider,
)
from documind.services.ingestion import IngestService
from documind.services.retrieval import RetrievalService
from documind.config import settings
from documind.db.session import get_async_session
from documind.embeddings.adapter import build_embedding_adapter
from documind.adapter.chat import build_chat_adapter


router = APIRouter()


def _services(request: Request) -> tuple[IngestService, RetrievalService]:
    state = request.app.state
    embedder = state.embedder
    chat = getattr(state, "chat_adapter", None)
    if chat is None:
        chat = build_chat_adapter(
            Provider.openai,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_chat_model=settings.OPENAI_CHAT_MODEL,
        )
        state.chat_adapter = chat
    ingest = IngestService(
        engine=state.engine,
        embedder=embedder,
    )
    retrieval = RetrievalService(
        engine=state.engine,
        embedder=embedder,
        chat_adapter=chat,
    )
    return ingest, retrieval


@router.post("/ingest", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(payload: IngestRequest, request: Request, session: AsyncSession = Depends(get_async_session)):
    ingest, _ = _services(request)
    created = await ingest.ingest(payload)
    return DocumentOut(
        id=created.id,
        title=created.title,
        status=created.status,
        metadata=created.metadata,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )


@router.get("/documents/{document_id}", response_model=DocumentOut)
async def get_document(document_id: str, session: AsyncSession = Depends(get_async_session)):
    document = (await session.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")
    return DocumentOut(
        id=document.id,
        title=document.title,
        status=document.status.value if hasattr(document.status, "value") else document.status,
        metadata=document.doc_metadata,
        created_at=document.created_at.isoformat() if hasattr(document.created_at, "isoformat") else document.created_at,
        updated_at=document.updated_at.isoformat() if hasattr(document.updated_at, "isoformat") else document.updated_at,
    )


@router.post("/ask", response_model=AskResponse)
async def ask(question: AskRequest, request: Request):
    _, retrieval = _services(request)
    return await retrieval.ask(question)
