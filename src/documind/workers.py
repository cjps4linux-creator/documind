from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

from celery import Celery
from documind.config import settings
from documind.schemas import IngestRequest, Provider
from documind.services.ingestion import IngestService
from documind.db.engine import engine as default_engine
from documind.embeddings.adapter import build_embedding_adapter


celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_routes={"documind.*": {"queue": "ingest"}},
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)


def _asyncio_run(fn, *args, **kwargs):
    return asyncio.run(fn(*args, **kwargs))


def _run_async(fn, *args, **kwargs):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(fn(*args, **kwargs))
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_asyncio_run, fn, *args, **kwargs).result()


@celery_app.task(name="documind.ingest")
def ingest(payload: dict[str, Any]) -> dict[str, Any]:
    provider = Provider(payload.get("embedding_provider", "openai"))
    api_key = settings.OPENAI_API_KEY if provider == Provider.openai else None
    service = IngestService(
        engine=default_engine,
        embedder=build_embedding_adapter(
            provider,
            api_key=api_key,
            region=settings.AWS_REGION,
        ),
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    request = IngestRequest(**payload)
    document = _run_async(service.ingest, request)
    return document.model_dump(mode="json")
