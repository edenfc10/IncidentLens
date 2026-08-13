# IncidentLens

IncidentLens is a privacy-first platform for investigating software incidents using repository code, stack traces, logs, runtime evidence, hybrid retrieval, and RAG.

The system is designed to return evidence-grounded diagnoses with references to relevant files, symbols, and code lines, while keeping private repositories isolated and protected.

## Planned technology stack

- Backend: Python, Django, Django REST Framework
- Frontend: Next.js, TypeScript
- Database: PostgreSQL with pgvector
- Background processing: Celery and Redis
- Code analysis: Python AST / Tree-sitter
- Retrieval: exact matching, full-text search, vector search, and reranking
- Infrastructure: Docker Compose and GitHub Actions

## Project documentation

- [System specification](outputs/incidentlens-system-specification.md)
- [Portfolio specification](outputs/incidentlens-portfolio-specification-v2.md)
- [Data model and API design](outputs/incidentlens-data-api-design-v1.md)

## Initial development order

1. Project infrastructure and development environment
2. Authentication, sessions, organizations, and permissions
3. Workspaces and secure repository connection
4. Incident and evidence intake
5. Repository parsing and indexing
6. Hybrid retrieval and RAG investigation pipeline
7. Evaluation, security hardening, and portfolio demo

## Current status

Architecture and planning are complete. Initial infrastructure implementation is the next milestone.
