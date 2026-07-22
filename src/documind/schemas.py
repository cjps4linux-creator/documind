from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class ChunkStatus(str, Enum):
    pending = "pending"
    indexed = "indexed"
    failed = "failed"


class Provider(str, Enum):
    openai = "openai"
    bedrock = "bedrock"


class IngestRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000_000)
    title: Optional[str] = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)
    chunk_size: Optional[int] = Field(default=None, ge=64, le=4096)
    chunk_overlap: Optional[int] = Field(default=None, ge=0, le=1024)
    embedding_provider: Provider = Provider.openai


class DocumentOut(BaseModel):
    id: str
    title: Optional[str]
    status: str
    metadata: dict
    created_at: str
    updated_at: str


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=6, ge=1, le=32)
    min_score: float = Field(default=0.25, ge=0.0, le=2.0)
    provider: Provider = Provider.openai
    include_chunks: bool = True


class Citation(BaseModel):
    chunk_id: int
    document_id: str
    title: Optional[str]
    text: str
    score: float


class AskResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    provider: Provider
    retrieved_chunks: int


class EvalCase(BaseModel):
    query: str
    expected_contains: list[str]


class EvalSuite(BaseModel):
    suite_id: str
    cases: list[EvalCase]


class EvalResult(BaseModel):
    suite_id: str
    cases: list[dict]
    pass_count: int
    fail_count: int
    mean_score: float
