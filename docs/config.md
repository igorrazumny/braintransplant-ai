<!-- Project: braintransplant-ai — File: CONFIG.md -->

# Config — braintransplant-ai

## 0) Scope & Ownership
- Repo: **private / proprietary** (see LICENSE.txt).
- Owner: Razum GmbH (brand: RazumAI).
- Purpose: local-first chat with memory + RAG (NotebookLM-like). Supports G Drive-sourced RAG, multi-model querying, and optional response aggregation. White-label UI mode for client deployments.

## 1) Data Handling
- Accepted sources: Google Drive folders (user-selected), local files under `data/docs/` (mounted), and pasted text.
- Stored artifacts: chats, per-message metadata, extracted text, chunk maps, embeddings, citations.
- PII: never required by system; if present in user data, it remains in the user’s tenant only. No sharing across tenants.

## 2) Environments
- Local dev: Python 3.11, Docker (Compose), `requirements.txt`.
- Services: `app` (Streamlit), `db` (Postgres 16).
- Ports: app `8502` (host).
- OS: macOS primary (developer machine), Linux in containers.

## 3) Secrets & Paths
- Secrets: `.env` (gitignored). Required at runtime:
  - `GEMINI_STUDIO_API_KEY` (if provider = Gemini)
  - Provider-specific keys as introduced (OpenAI, Anthropic, etc.)
- Paths (host-mounted):
  - `data/` — user docs, staged imports (ignored).
  - `outputs/` — exports, logs (ignored).

## 4) RAG
- Ingestion: select G Drive folder(s) or drop files into `data/docs/`.
- Supported types (initial): PDF, DOCX, MD, TXT, CSV. Images via OCR (future).
- Chunking: deterministic, length-aware with overlap; metadata preserved (doc id, page, section).
- Embeddings: provider-specific vectors; dimensions recorded per provider/model.
- Retrieval: top-k + MMR + metadata filters (doc scope/date/type).
- Citations: page/section-level refs surfaced in UI.

## 5) Chat & Memory
- Session threads: persistent; each message records model id, prompt template version, and RAG context used.
- History RAG: user can include prior messages/files as retrieval sources per session.
- Export: per-thread JSONL and Markdown transcripts to `outputs/`.

## 6) Multi-Model & Aggregation
- Providers: start with Gemini; add OpenAI/Claude/Mistral incrementally.
- Fan-out: optional parallel queries to multiple models for a prompt.
- Aggregator: one model (or heuristic) summarizes/compares returns; provenance kept per model.

## 7) White-Label Mode
- Tenant branding, simplified UI, fixed provider/model selection, and tenant-scoped storage.
- No cross-tenant data access. Admin-set tokens, no on-screen secrets.

## 8) Security & Compliance
- Secrets never committed. Environment-only API keys.
- Data locality: tenant data stays within its DB schema and mounted volume.
- Deletion: per-document purge deletes chunks, embeddings, and citations.
- Audit trail: ingestion and chat actions timestamped with actor/session ids.

## 9) Versioning
- App versioning via git tags.
- Prompt templates versioned; message records store template version + model id.
- Vector indexes rebuilt on schema/embedding-model change; previous index retained until migration completes.

## 10) Operations
- Startup: `make redeploy` (build+start), `make psql` (DB shell).
- Reset: `make redeploy-hard` (drops volumes) when changing DB bootstrap vars.
- Schema management: `make redeploy-clean` to recreate `public` and reapply schema.

## 11) Contacts
- Tech/Owner: Igor Razumny (Razum GmbH / RazumAI)
- Legal/License: see LICENSE.txt
