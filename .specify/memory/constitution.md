<!--
Sync Impact Report
==================
Version change: N/A → 1.0.0
Modified principles: N/A (initial ratification)
Added sections:
  - Core Principles (3 principles)
  - Technology Stack
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no update needed (template references
    constitution dynamically via Constitution Check section)
  - .specify/templates/spec-template.md ✅ no update needed (template is generic)
  - .specify/templates/tasks-template.md ✅ no update needed (template is generic)
  - No commands/ directory exists — skipped
Follow-up TODOs: None
-->

# Multimodal RAG POC Constitution

## Core Principles

### I. POC-First Simplicity

All design decisions MUST favor the simplest viable approach.
This is a proof-of-concept — its purpose is to validate the
vision-based RAG pipeline, not to build production infrastructure.

- MUST NOT introduce abstraction layers, plugin systems, or
  configuration frameworks ahead of a concrete second use case.
- MUST NOT add OCR or text-extraction pipelines; the vision-native
  embedding approach (ColPali) is the hypothesis under test.
- MUST prefer inline code over indirection. A 30-line script that
  works is better than a 5-file package that's "extensible."
- New dependencies MUST justify themselves against the alternative
  of writing the functionality inline.

### II. Retrieval Quality as the North Star

The primary success metric is retrieval relevance. Every pipeline
change MUST be evaluated against measurable retrieval quality.

- MUST define an evaluation dataset (query + expected document
  pairs) before claiming any retrieval configuration is "better."
- MUST report at least one rank-aware metric (Recall@k, MRR, or
  NDCG) when comparing retrieval approaches.
- MUST NOT merge changes that degrade retrieval metrics on the
  evaluation set without explicit justification and sign-off.
- Generation quality (LLM answer accuracy) is secondary to
  retrieval quality — a correct retrieval with a mediocre answer
  is more valuable than hallucinated fluency over wrong documents.

### III. End-to-End Pipeline Integrity

The full pipeline — ingest → embed → store → retrieve → generate —
MUST be runnable end-to-end at all times.

- MUST NOT commit partial pipeline stages that leave the chain
  broken (e.g., an embedder with no retrieval path wired up).
- MUST maintain a single-command or single-script path to run the
  complete pipeline from raw documents to a generated answer.
- Every new component MUST be demonstrated working within the
  full pipeline, not just in isolation.

## Technology Stack

The POC is built on the following stack. Swapping a component
MUST be justified by a retrieval quality improvement or a
blocking technical limitation — not by preference.

- **Embeddings**: ColPali (vision-native document embeddings)
- **Vector store**: Qdrant
- **Inference**: vLLM-Omni serving Qwen3-VL
- **Language**: Python

## Development Workflow

- Commits SHOULD be small and focused on a single pipeline stage
  or evaluation change.
- Evaluation results (metrics, sample outputs) SHOULD be captured
  alongside the code change that produced them — in commit
  messages, PR descriptions, or a `results/` directory.
- Experiments that do not improve retrieval metrics SHOULD still
  be documented (what was tried, what the numbers showed) to
  avoid re-running dead ends.

## Governance

This constitution defines the non-negotiable principles for the
multimodal RAG POC. All implementation decisions, code reviews,
and spec plans MUST verify compliance with the principles above.

- **Amendments**: Any change to this constitution MUST be
  documented with a version bump, rationale, and updated date.
- **Versioning**: Semantic versioning (MAJOR.MINOR.PATCH).
  MAJOR = principle removal or redefinition; MINOR = new
  principle or material expansion; PATCH = wording/clarification.
- **Compliance**: The `/speckit-plan` Constitution Check gate
  MUST validate against these principles before implementation
  begins.

**Version**: 1.0.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-03
