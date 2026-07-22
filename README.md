# DocuMind

AI document intelligence platform with RAG, FastAPI, async workers, and pgvector.

## Architecture
- API: FastAPI + async SQLAlchemy
- Workers: Celery + Redis
- Embeddings: OpenAI + Amazon Bedrock adapters with factory selection
- Retrieval: pgvector cosine similarity via RAG pipeline
- Evaluation: golden eval harness with faithfulness, grounding, and MRR@k

## Local setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
python -m pytest tests/ -q
```

## ADRs
- pgvector over managed vector DBs: simpler topology, same ACID guarantees.
- Celery/Redis over Airflow: direct FastAPI integration, lower ops overhead for ingestion frequency.
- SQLAlchemy 2.0 async ORM with explicit table inserts for SQLite compatibility.
