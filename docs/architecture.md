# Architecture

DocuMind is split into three primary runtime identities within a single source tree:

- `src/documind/app.py`: FastAPI application exposing REST endpoints and the shared `app.state`.
- `src/documind/workers.py`: Celery worker task `documind.ingest` that performs long-running ingestion without blocking the API.
- `src/documind/routers.py`: Request-scoped service bindings derived from `app.state`, keeping service construction out of route handlers.

Services own business logic:
- `IngestService`: chunks input text, generates embeddings, persists documents and chunk embeddings in a PostgreSQL + pgvector database via async SQLAlchemy.
- `RetrievalService`: embeds the query, retrieves top-k chunks using cosine similarity, and asks the chat adapter for an answer with inline citations.

Adapters are provider-agnostic:
- `EmbeddingAdapter` and concrete `OpenAIEmbeddingAdapter`, `BedrockEmbeddingAdapter`.
- `ChatAdapter` and concrete `OpenAIChatAdapter`, `BedrockChatAdapter`.

Database models live under `src/documind/db/models.py` and are migrated with Alembic.

## Data Flow
1. POST `/ingest` -> `IngestService.ingest` -> chunking -> embeddings -> DB insert -> 202 Accepted.
2. POST `/ask` -> `RetrievalService.ask` -> query embed -> SQL similarity search -> chat completion -> citations -> response.

## Deployment Notes
API and worker are scannable independently. The worker is CPU-bound for chunking and async-bound for embedding/chat I/O, so thread pool/event loops are isolated carefully.
