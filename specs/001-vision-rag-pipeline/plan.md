# Implementation Plan: Vision-Based Multimodal RAG Pipeline

**Branch**: `001-vision-rag-pipeline` | **Date**: 2026-07-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-vision-rag-pipeline/spec.md`

## Summary

Build a vision-native RAG pipeline that ingests PDFs and images,
embeds page images using ColQwen2 (no OCR), stores multi-vector
embeddings in Qdrant, retrieves relevant pages via MaxSim late
interaction, and generates grounded answers using Qwen3-VL served
by vLLM. Gradio provides the upload and query UI. See
[research.md](research.md) for technology decisions.

## Technical Context

**Language/Version**: Python >= 3.10

**Primary Dependencies**:
- `colpali-engine` — ColQwen2 embedding model
- `qdrant-client` — vector store with multi-vector/MaxSim support
- `pymupdf` — PDF page rendering (no system deps)
- `gradio` — web UI for upload and query
- `openai` — client for vLLM's OpenAI-compatible API
- `vllm` >= 0.11.0 — serves Qwen3-VL for answer generation
- `torch`, `Pillow` — core ML and image handling

**Storage**: Qdrant in-memory (`QdrantClient(":memory:")`) for POC.
No database. No file persistence across restarts.

**Testing**: pytest (manual validation scenarios in
[quickstart.md](quickstart.md))

**Target Platform**: Local machine with NVIDIA GPU (CUDA)

**Project Type**: Web application (Gradio-based single-page app)

**Performance Goals**: Not a priority for POC. Correctness and
demonstrability over speed.

**Constraints**: 3-day POC scope. Single user. No auth. No OCR.
GPU with >= 20GB VRAM (8B model) or >= 12GB (4B fallback).

**Scale/Scope**: Tens to hundreds of pages. Single concurrent user.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1
design.*

### I. POC-First Simplicity ✅

- No abstraction layers or plugin systems introduced.
- No OCR or text extraction anywhere in the pipeline.
- Single-file app structure preferred. Modules only where the
  pipeline stages genuinely differ (ingest, retrieve, generate).
- All dependencies justified: each maps to a core pipeline stage
  with no inline alternative.

### II. Retrieval Quality as the North Star ✅

- Data model includes evaluation-ready structures
  (RetrievalResult with scores).
- Quickstart defines validation scenarios for retrieval accuracy.
- Success criteria SC-002 sets measurable Recall@5 threshold (80%).
- Spec requires evaluation dataset before claiming quality.

### III. End-to-End Pipeline Integrity ✅

- Pipeline flows end-to-end: ingest → embed → store → retrieve →
  generate.
- Quickstart validates the full chain in Scenario 1.
- Single-command launch: `python app.py` (after vLLM server).
- No partial implementations — all pipeline stages designed
  together.

## Project Structure

### Documentation (this feature)

```text
specs/001-vision-rag-pipeline/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── pipeline.md
└── tasks.md              # Created by /speckit-tasks
```

### Source Code (repository root)

```text
src/
├── ingest.py             # PDF rendering + ColQwen2 embedding + Qdrant upsert
├── retrieve.py           # Query embedding + Qdrant MaxSim search
├── generate.py           # vLLM/Qwen3-VL answer generation
└── config.py             # Model names, Qdrant settings, vLLM URL

app.py                    # Gradio UI (entry point)
requirements.txt          # Pinned dependencies

eval/
├── queries.json          # Evaluation query-document pairs
└── evaluate.py           # Recall@k / MRR scoring script
```

**Structure Decision**: Single project layout. Flat `src/` with one
module per pipeline stage. `app.py` at root as the Gradio entry
point. `eval/` directory for retrieval quality measurement per
constitution principle II.

## Complexity Tracking

No constitution violations. No complexity justification needed.
