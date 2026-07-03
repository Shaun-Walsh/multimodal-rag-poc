# Tasks: Vision-Based Multimodal RAG Pipeline

**Input**: Design documents from `specs/001-vision-rag-pipeline/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/pipeline.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Omitted.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Exact file paths included in every task

## Phase 1: Setup

**Purpose**: Project initialization and dependency management

- [x] T001 Create project directory structure: `src/`, `eval/`, and empty `__init__.py` files per plan.md layout
- [x] T002 [P] Create `requirements.txt` with pinned dependencies: `colpali-engine`, `qdrant-client`, `pymupdf`, `Pillow`, `gradio`, `openai`, `torch`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create `src/config.py` with constants: ColQwen2 model name (`vidore/colqwen2-v1.0`), Qdrant collection name, embedding dimension (128), vLLM base URL (`http://localhost:8000/v1`), Qwen3-VL model name, default top_k (5), and supported file extensions
- [x] T004 [P] Implement ColQwen2 model and processor loading in `src/config.py`: function `get_model()` that loads `ColQwen2.from_pretrained` with `torch.bfloat16` and returns `(model, processor)` tuple, cached after first call
- [x] T005 [P] Implement Qdrant collection initialization in `src/config.py`: function `get_qdrant_client()` that creates an in-memory `QdrantClient`, creates collection with `MultiVectorConfig(comparator=MAX_SIM)`, vector size 128, distance COSINE, HNSW m=0; returns client (cached after first call)

**Checkpoint**: Foundation ready — model loads, Qdrant collection exists

---

## Phase 3: User Story 1 — Upload and Ingest Documents (Priority: P1) MVP

**Goal**: User uploads PDFs/images, system renders pages, embeds them with ColQwen2, and stores multi-vectors in Qdrant

**Independent Test**: Upload a 10-page PDF and verify all 10 pages appear as points in Qdrant with correct metadata

### Implementation for User Story 1

- [x] T006 [US1] Implement `render_pdf_pages(file_path: str) -> list[PIL.Image]` in `src/ingest.py`: use PyMuPDF to open PDF, render each page at 300 DPI (matrix scale 300/72), return list of PIL Images; for image files (PNG/JPG/JPEG) return single-element list with `Image.open()`
- [x] T007 [US1] Implement `embed_images(images: list[PIL.Image]) -> list[np.ndarray]` in `src/ingest.py`: use `get_model()` from config, call `processor.process_images(images)`, run through model in `torch.no_grad()`, return list of numpy arrays each shape (N, 128)
- [x] T008 [US1] Implement `ingest_document(file_path: str) -> int` in `src/ingest.py`: validate file extension against config.SUPPORTED_EXTENSIONS, call `render_pdf_pages()`, call `embed_images()`, upsert each page as a Qdrant point with multi-vector embeddings and payload (doc_id, filename, page_number, base64-encoded JPEG of page image), return number of pages ingested; raise `ValueError` for unsupported file types or corrupted files
- [x] T009 [US1] Create Gradio upload interface in `app.py`: `gr.File(file_count="multiple", file_types=[".pdf",".png",".jpg",".jpeg"])` input, `gr.Textbox` for status output, wire upload button to call `ingest_document()` for each file, display progress and final count of pages ingested; handle errors with user-friendly messages

**Checkpoint**: User can upload documents and they are embedded and stored. Verify by checking Qdrant point count matches expected page count.

---

## Phase 4: User Story 2 — Query and Retrieve Relevant Pages (Priority: P1)

**Goal**: User types a natural language query, system retrieves the most relevant page images ranked by MaxSim score

**Independent Test**: Ingest a known document, ask a question whose answer is on a specific page, verify that page appears in top 5 results

### Implementation for User Story 2

- [x] T010 [US2] Implement `embed_query(query: str) -> np.ndarray` in `src/retrieve.py`: use `get_model()` from config, call `processor.process_queries([query])`, run through model, return numpy array shape (T, 128) where T is token count
- [x] T011 [US2] Implement `retrieve(query: str, top_k: int = 5) -> list[dict]` in `src/retrieve.py`: call `embed_query()`, call `client.query_points()` on the Qdrant collection with `using="colpali"` and `limit=top_k`, decode base64 page images from payload, return list of dicts with keys: page_id, doc_id, filename, page_number, score, image (PIL.Image)
- [x] T012 [US2] Add query interface to `app.py`: `gr.Textbox` for query input, `gr.Gallery` to display retrieved page images with captions showing filename, page number, and score; wire query button to call `retrieve()`, handle empty-collection case with "No documents uploaded yet" message

**Checkpoint**: User can query and see ranked page images. Verify correct page appears in results for a known query.

---

## Phase 5: User Story 3 — Grounded Answer Generation (Priority: P2)

**Goal**: After retrieval, system passes top-k page images + query to Qwen3-VL via vLLM and displays a grounded answer alongside source pages

**Independent Test**: Ask a factual question, verify the generated answer references content visible on the retrieved pages

### Implementation for User Story 3

- [x] T013 [US3] Implement `generate_answer(query: str, pages: list[dict]) -> str` in `src/generate.py`: create OpenAI client pointing at vLLM base URL from config, build chat message with multiple `image_url` content blocks (base64-encoded JPEGs from retrieved pages) plus text block with query and instruction to answer based on the provided pages, call `chat.completions.create()` with the Qwen3-VL model name, return `choices[0].message.content`; handle connection errors gracefully with fallback message
- [x] T014 [US3] Integrate answer generation into query flow in `app.py`: after `retrieve()` returns results, call `generate_answer()` with query and retrieved pages, display generated answer in `gr.Markdown` component below the image gallery, show source page references (filename + page number) alongside the answer; if vLLM is unavailable, display retrieval results only with a note that generation is offline

**Checkpoint**: Full pipeline works end-to-end: upload → query → retrieved pages + generated answer. Verify answer references visible page content.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Evaluation tooling and final validation

- [x] T015 [P] Create evaluation dataset in `eval/queries.json`: define 20 query-document pairs with fields: query (str), expected_doc (str), expected_page (int); use documents from a test corpus to be uploaded manually
- [x] T016 [P] Create evaluation script in `eval/evaluate.py`: load `eval/queries.json`, ingest test documents, run each query through `retrieve()`, compute Recall@5 and MRR, print results table; target: Recall@5 >= 0.80 per SC-002
- [x] T017 Run quickstart validation scenarios from `specs/001-vision-rag-pipeline/quickstart.md` end-to-end: verify all 5 scenarios pass (single PDF upload, mixed upload, retrieval quality, empty collection, unsupported file type)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (needs model + Qdrant)
- **US2 (Phase 4)**: Depends on Phase 2 (needs model + Qdrant) — can run parallel with US1 for code, but needs ingested data to demonstrate
- **US3 (Phase 5)**: Depends on Phase 4 (needs retrieve() to be working)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Can start coding after Phase 2 — independent from US1 in code, but demo requires US1 data
- **US3 (P2)**: Depends on US2 retrieve() being functional — extends the query flow

### Within Each User Story

- Models/data functions before orchestrators
- Core logic before UI integration
- Each task builds on the previous within its story

### Parallel Opportunities

- T001 and T002 can run in parallel (Setup phase)
- T004 and T005 can run in parallel (Foundational phase — different functions in config.py)
- T015 and T016 can run in parallel (Polish phase — different files)
- US1 and US2 implementation code can be written in parallel (different files: ingest.py vs retrieve.py)

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Upload + Ingest)
4. **STOP and VALIDATE**: Upload a PDF, check Qdrant point count
5. Complete Phase 4: User Story 2 (Query + Retrieve)
6. **STOP and VALIDATE**: Query and verify correct pages returned
7. Deploy/demo if retrieval quality is sufficient

### Full Pipeline

8. Complete Phase 5: User Story 3 (Answer Generation)
9. **VALIDATE**: Full end-to-end demo
10. Complete Phase 6: Evaluation tooling
11. Run evaluation: target Recall@5 >= 0.80

### Incremental Delivery

- After US1: "I can ingest documents" (foundation demo)
- After US2: "I can find the right page" (core value demo)
- After US3: "I can answer questions with sources" (full pipeline demo)
- After Polish: "I can measure retrieval quality" (evaluation-ready)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps each task to its user story for traceability
- Each user story is independently testable at its checkpoint
- Commit after each task or logical group
- vLLM server must be running separately for US3 (see quickstart.md)
- Total estimated effort: fits within 3-day POC scope
