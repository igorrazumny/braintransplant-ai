# braintransplant-ai

AI assistant with cross-model memory and RAG.

## Persistent volumes
- `braintransplant-ai_pgdata` — PostgreSQL cluster (named Docker volume)

## Required config
- `.config/gcp_service_account.json` — GCP service account key with Vertex AI + Storage access
