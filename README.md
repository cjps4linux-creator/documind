# DocuMind

AI document intelligence platform with RAG, FastAPI, async workers, and pgvector.

## Architecture
- API: FastAPI + async SQLAlchemy
- Workers: Celery + Redis
- Embeddings: OpenAI + Amazon Bedrock adapters
- Retrieval: pgvector cosine similarity
- Evaluation: golden eval harness

## Local setup
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e ".[dev]"
cp .env.example .env
python -m pytest tests/ -q
```

## ADRs
- pgvector over managed vector DBs: simpler topology, same ACID guarantees.
- Celery/Redis over Airflow: direct FastAPI integration, lower ops overhead for ingestion frequency.
