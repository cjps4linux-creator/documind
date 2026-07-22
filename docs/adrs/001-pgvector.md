# ADR-001: Use pgvector instead of a dedicated vector database

## Status
Accepted

## Context
We need vector search for retrieved chunks. Alternatives included Pinecone, Weaviate, Qdrant, and pgvector.

## Decision
Choose pgvector inside PostgreSQL.

## Consequences
- Fewer services to operate.
- Backups and access control stay consistent.
- Suitable for early-scale RAG workloads.
