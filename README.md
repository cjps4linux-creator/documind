# DocuMind

AI document intelligence platform  -  ingest, embed, retrieve, and reason over unstructured business documents with a production-grade FastAPI backend, Celery workers, pgvector semantic search, and a golden eval harness.

Built by Conrad CJ Wilson.

## What It Demonstrates

| Capability | Implementation |
|---|---|
| Document ingestion ETL | Async chunking with metadata extraction |
| Embedding pipeline | OpenAI + Amazon Bedrock adapters with factory selection |
| Vector search | pgvector cosine similarity with metadata filtering |
| RAG retrieval | Hybrid search combining vector similarity and keyword match |
| Grounded generation | LLM answers with required citation gates |
| Evaluation harness | Golden eval measuring faithfulness, grounding, and MRR@k |
| Async workers | Celery + Redis for offloaded ingestion and evaluation |
| API contracts | Strict Pydantic schemas with OpenAPI documentation |
| Observability | Structured logging, correlation IDs, `/metrics` endpoint |
| Production hardening | OAuth2 refresh-token rotation, rate limiting, RBAC |

## Stack

| Layer | Tooling |
|---|---|
| Language | Python 3.11 |
| API | FastAPI + async SQLAlchemy 2.0 |
| Workers | Celery + Redis |
| Vector store | PostgreSQL + pgvector |
| Embeddings | OpenAI `text-embedding-3-small`, Amazon Bedrock Titan |
| LLM | OpenAI Chat Completions, Amazon Bedrock Converse |
| Evaluation | Custom golden eval harness (faithfulness, grounding, MRR@k) |
| Testing | pytest with async fixtures |
| Linting | ruff |
| Infrastructure | Docker Compose, Kubernetes manifests |
| CI | GitHub Actions (lint, test, build, security scan) |
| Monitoring | Prometheus `/metrics`, structured JSON logs |

## Architecture

```
User / Client
    │
    ▼
FastAPI API Layer
    │
    ├── POST /ingest ──▶ Chunker ──▶ Embedder (OpenAI | Bedrock)
    │                              │
    │                              ▼
    │                        pgvector (PostgreSQL)
    │
    ├── POST /query ──▶ Embedder ──▶ Retriever (vector + metadata filter)
    │                              │
    │                              ▼
    │                        RAG Pipeline
    │                              │
    │                    ┌─────────┴──────────┐
    │                    ▼                    ▼
    │              Graph Paths          Grounded Generation
    │                    │                    │
    │                    └─────────┬──────────┘
    │                              ▼
    │                        Answer + Citations
    │
    ├── GET  /eval ──▶ Golden eval harness
    │
    └── Celery Workers (async ingestion, evaluation jobs)
                │
                ▼
          Redis Broker
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ with pgvector extension
- Redis 7+
- OpenAI API key or AWS credentials with Bedrock access

### Installation

```bash
git clone https://github.com/cjps4linux-creator/documind.git
cd documind

python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate   # Linux/macOS

pip install -e ".[dev]"
cp .env.example .env
```

### Configuration

Set the following environment variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis broker URL |
| `OPENAI_API_KEY` | OpenAI API key (optional if using Bedrock) |
| `AWS_REGION` | AWS region for Bedrock (optional if using OpenAI) |
| `BEDROCK_MODEL` | Bedrock model [lorem] (optional) |
| `EMBEDDING_PROVIDER` | `openai` or `bedrock` |
| `CELERY_BROKER_URL` | Redis URL for Celery |
| `CELERY_RESULT_BACKEND` | Redis URL for task results |

### Run

```bash
# Start infrastructure
docker compose up -d postgres redis

# Run database migrations
alembic upgrade head

# Start the API
uvicorn documind.app:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal, start the Celery worker
celery -A documind.workers worker --loglevel=info
```

### Verify

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Tests

```bash
pytest tests/ -q
```

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/ingest` | Ingest a document (chunk + embed + store) |
| POST | `/query` | RAG query (returns grounded answer + citations) |
| GET | `/graph?entity=` | Knowledge-graph relations for an entity |
| GET | `/eval` | Retrieval/answer quality metrics |
| POST | `/reset` | Clear ingested state |
| GET | `/health` | Service health check |
| GET | `/metrics` | Prometheus metrics |

## Architecture Decision Records

### ADR-001: pgvector Over Managed Vector Databases

pgvector was selected over Pinecone, Weaviate, and ChromaDB because it provides equivalent vector search capabilities while maintaining ACID guarantees through PostgreSQL. This simplifies the deployment topology  -  one database instead of two  -  and keeps access control, backups, and audit logging consistent.

### ADR-002: Celery/Redis Over Airflow

Celery was selected over Airflow because it integrates directly with the FastAPI application lifecycle, has lower operational overhead for the ingestion frequency this platform requires, and avoids the overhead of a full DAG scheduler for what is fundamentally an async task queue.

### ADR-003: SQLAlchemy 2.0 Async ORM

SQLAlchemy 2.0 async patterns were selected to maintain [lorem]-blocking database access across the API and worker layers. Explicit table inserts are used for SQLite compatibility in test environments, while the production path uses native async PostgreSQL drivers.

### ADR-004: Dual LLM Provider Support

The adapter factory pattern supports both OpenAI and Amazon Bedrock without changing the retrieval, grounding, or evaluation contracts. This prevents vendor lock-in and allows production traffic to shift between providers without re-architecting the pipeline.

## Honest Limitations

- The golden eval harness uses lexical-overlap metrics for faithfulness; production deployments should swap in an NLI/entailment scorer for higher accuracy.
- The current chunking strategy is fixed-size with overlap; production workloads may benefit from semantic chunking based on document structure.
- OAuth2 refresh-token rotation is implemented but not yet exercised against a live identity provider.
- Kubernetes manifests are provided for reference; production hardening (network policies, PodSecurity standards, external secrets) requires environment-specific configuration.

## Deployment

### Docker Compose

```bash
docker compose up -d
```

Services: `postgres` (pgvector), `redis`, `api`, `worker`.

### Kubernetes

Manifests are provided under `k8s/`:

- `api-deployment.yaml`  -  API server with probes and resource limits
- `worker-deployment.yaml`  -  Celery worker with concurrency tuning
- `hpa.yaml`  -  Horizontal pod autoscaling based on CPU and memory
- `configmap.yaml`  -  Environment configuration

## Testing Strategy

- **Unit tests**: Adapter behavior, schema validation, chunking logic
- **Integration tests**: API endpoints with test database, worker job execution
- **Eval tests**: Golden eval harness with held-out question/answer pairs
- **Contract tests**: Pydantic schema enforcement across all endpoints

## Current State

Production-ready prototype. Core RAG pipeline, async workers, pgvector retrieval, and eval harness are implemented and tested. The platform is deployable with Docker Compose and has Kubernetes manifests prepared for production orchestration.

## License

MIT  -  use, modify, and ship freely.

**Author:** Conrad CJ Wilson
**GitHub:** https://github.com/cjps4linux-creator
**LinkedIn:** https://www.linkedin.com/in/conradcjwilson
