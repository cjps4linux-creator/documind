# Architecture

## System overview
- FastAPI app exposes `/ingest`, `/documents/{id}`, `/ask`, `/healthz`
- Ingestion chunks documents, embeds chunks, stores documents/chunks/embeddings
- Retrieval uses pgvector cosine similarity over stored embeddings
- Chat synthesizes answers from retrieved chunks with inline citations
- Celery workers provide async ingestion and embedding offload
