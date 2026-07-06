# Implementation Plan: NotebookLM-Style UI

**Branch**: `feat/notebook-ui` | **Date**: 2026-07-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-notebook-ui/spec.md`

## Summary

Enhance the existing multimodal RAG POC with a NotebookLM-style
user experience: a document library panel with delete capability, a
multi-turn chat interface replacing the single-shot query box, and
inline source citations in generated answers. All changes are UI and
orchestration layer — the core pipeline (ColQwen2 embeddings, Qdrant
storage, Qwen3-VL generation via vLLM) is unchanged.

## Technical Context

**Language/Version**: Python 3.x (same as existing POC)

**Primary Dependencies**: gradio>=4.0.0 (Chatbot + Blocks), openai
(vLLM client), qdrant-client (deletion API), colpali-engine,
pymupdf, Pillow, torch, numpy — no new dependencies required.

**Storage**: Qdrant in-memory (existing). New in-memory dict for
document registry (no persistence across restarts).

**Testing**: Manual validation via quickstart scenarios. No automated
test suite per POC scope.

**Target Platform**: Linux server with GPU (H100), accessed via
browser.

**Project Type**: Web application (Gradio)

**Performance Goals**: Library panel loads in <1 second (SC-001).
Chat responses depend on existing pipeline latency.

**Constraints**: No persistence across restarts. Single-user session.
Conversation history bounded to 10 recent exchanges. Existing
pipeline untouched.

**Scale/Scope**: Single-user POC. Document collections up to ~100
documents / ~1000 pages.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1
design.*

### Principle I: POC-First Simplicity

**Status**: PASS

- Document registry is a plain dict — no ORM, no database.
- Multi-turn retrieval uses simple query concatenation — no extra
  VLM call or complex reformulation pipeline.
- Citation prompting uses numbered source labels in the VLM prompt —
  no post-processing NLP.
- No new dependencies added.
- All state is session-scoped and in-memory.

### Principle II: Retrieval Quality as North Star

**Status**: PASS

- Core retrieval pipeline (ColQwen2 + Qdrant MaxSim) is unchanged.
- Multi-turn query concatenation may slightly improve follow-up
  retrieval by providing context, but does not degrade baseline
  single-turn retrieval.
- Existing evaluation tooling (`eval/evaluate.py`) remains valid.

### Principle III: End-to-End Pipeline Integrity

**Status**: PASS

- The full pipeline (ingest → embed → store → retrieve → generate)
  remains functional throughout. Changes are additive: document
  deletion is a new capability on the storage layer, chat is a new
  UI on top of existing retrieve + generate, citations are a prompt
  modification.
- Each change can be validated end-to-end via quickstart scenarios.

## Project Structure

### Documentation (this feature)

```text
specs/002-notebook-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── ui.md            # UI contracts
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py            # Constants (unchanged)
├── ingest.py            # + document registry, delete_document()
├── retrieve.py          # + history-aware query building
├── generate.py          # + conversation history, citation prompt
└── library.py           # NEW: document library functions

app.py                   # Major rewrite: sidebar + chat layout
requirements.txt         # Unchanged (no new deps)
eval/
├── evaluate.py          # Unchanged
└── queries.json         # Unchanged
```

**Structure Decision**: Existing flat `src/` module structure is
preserved. One new file `src/library.py` is added for document
registry management — this isolates library state from the ingestion
logic while remaining minimal. The alternative (adding registry
functions to `ingest.py`) would mix document management concerns with
the embedding pipeline.

### Key Changes by File

| File | Change Type | Description |
|------|-------------|-------------|
| `src/library.py` | NEW | Document registry (in-memory dict), `list_documents()`, `delete_document()` |
| `src/ingest.py` | MODIFY | Call `register_document()` after successful ingest |
| `src/retrieve.py` | MODIFY | Add `build_contextualized_query()` for multi-turn |
| `src/generate.py` | MODIFY | Accept conversation history, citation-numbered prompt |
| `app.py` | REWRITE | Sidebar + chat layout, multi-turn state management |
