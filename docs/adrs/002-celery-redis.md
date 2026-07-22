# ADR-002: Use Celery with Redis for asynchronous ingestion

## Status
Accepted

## Context
Ingestion and embedding can be long-running.

## Decision
Use Celery with Redis as broker and result backend.

## Consequences
- Simple worker scaling.
- Visible task state and retries.
