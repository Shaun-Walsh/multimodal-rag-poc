# Tasks: NotebookLM-Style UI

**Input**: Design documents from `specs/002-notebook-ui/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/ui.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Omitted.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Exact file paths included in every task

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Create `src/library.py` with document registry: module-level dict `_document_registry: dict[str, dict]` mapping `doc_id → {"filename": str, "page_count": int}`. Implement `register_document(doc_id: str, filename: str, page_count: int) → None` that adds an entry, `list_documents() → list[dict]` that returns all entries as `[{"doc_id", "filename", "page_count"}]`, and `delete_document(doc_id: str) → bool` that removes the document's points from Qdrant using `client.delete()` with `FilterSelector(Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]))` and removes the registry entry; returns True if found, False otherwise. Import `get_qdrant_client` and `QDRANT_COLLECTION_NAME` from `src/config`.
- [x] T002 Modify `src/ingest.py` to call `register_document(doc_id, filename, len(points))` from `src/library` after the successful `client.upsert()` call in `ingest_document()`. Add the import at the top of the file.

**Checkpoint**: Document registry works — ingest registers documents, list returns them, delete removes from Qdrant and registry.

---

## Phase 2: User Story 1 — Document Library Management (Priority: P1) MVP

**Goal**: User sees all uploaded documents with filename and page count in a sidebar, can delete any document to remove its pages from search

**Independent Test**: Upload 3 documents, verify all 3 appear in library with correct page counts, delete one, verify it disappears and its pages are no longer in search results

### Implementation for User Story 1

- [x] T003 [US1] Rewrite `app.py` with new two-column layout using `gr.Blocks`: left `gr.Column(scale=1)` as document library sidebar, right `gr.Column(scale=3)` as main content area. Sidebar contains: `gr.Markdown` title "Document Library", `gr.File(file_count="multiple", file_types=[".pdf",".png",".jpg",".jpeg"])` for upload, `gr.Button("Ingest Documents")` for upload trigger, `gr.HTML` component for library display showing a list of documents with filename, page count, and a delete button per document (rendered as an HTML table or list). Main content area: temporarily keep a simple `gr.Textbox` query input, `gr.Button("Search")`, `gr.Gallery` for results, and `gr.Markdown` for answer (placeholder until US2 replaces with chat). Implement `render_library()` function that calls `list_documents()` from `src/library` and returns HTML string — shows empty state message "No documents uploaded yet" when list is empty. Implement `handle_upload(files)` that calls `ingest_document()` for each file and returns updated library HTML. Implement `handle_delete(doc_id)` that calls `delete_document()` and returns updated library HTML. Wire `gr.Button` events. Keep `handle_query()` functional for the temporary query interface. Bind to `server_name="0.0.0.0"`.

**Checkpoint**: User can upload documents, see them in the sidebar library with page counts, delete them, and the simple query interface still works.

---

## Phase 3: User Story 2 — Multi-Turn Chat Interface (Priority: P1)

**Goal**: User types questions in a chat interface, follow-up questions resolve against prior context, full conversation history visible

**Independent Test**: Ask an initial question, then ask a follow-up using a pronoun ("Tell me more about that"), verify the system returns a contextually relevant answer

### Implementation for User Story 2

- [x] T004 [P] [US2] Add `build_contextualized_query(query: str, history: list[dict]) → str` to `src/retrieve.py`: if `history` is empty or has no prior user messages, return `query` unchanged; otherwise extract the last user message from history and prepend it to the current query separated by ` | ` (e.g., `"prior question | current question"`). This gives the embedding model context for follow-up queries with pronouns. Cap at last 2 user messages maximum.
- [x] T005 [P] [US2] Modify `generate_answer()` in `src/generate.py` to accept an optional `history: list[dict] | None = None` parameter. When history is provided, insert prior conversation exchanges (user/assistant pairs) into the chat messages list before the current user message with source images. Bound history to the last 10 exchanges (20 messages). Keep existing behavior when history is None for backward compatibility.
- [x] T006 [US2] Replace the temporary query interface in the right column of `app.py` with a multi-turn chat: add `gr.Chatbot(type="messages")` for conversation display, `gr.State(value=[])` for conversation history (list of `{"role", "content"}` dicts), `gr.Textbox(placeholder="Ask a question...")` for input, `gr.Button("Send")` and `gr.Button("Clear Chat")`. Implement `handle_message(query, history, chatbot_messages)`: validate query is non-empty, append user message to history, call `build_contextualized_query(query, history)` then `retrieve()`, call `generate_answer(query, results, history)`, append assistant response to history, update chatbot messages with user query and assistant answer, return updated chatbot, sources gallery, and history state. Implement `handle_clear()` that returns empty chatbot, empty gallery, empty history. Add `gr.Gallery` below chat for source page display. When no documents uploaded, return message "Please upload documents first." Wire Send button click and Textbox submit events to `handle_message()`. Wire Clear button to `handle_clear()`.

**Checkpoint**: User can have a multi-turn conversation. Follow-up questions with pronouns produce contextually relevant answers. Clear button resets conversation. Document library sidebar from US1 still works.

---

## Phase 4: User Story 3 — Inline Source Citations (Priority: P2)

**Goal**: Generated answers contain numbered citation markers [1], [2] that correspond to retrieved source page thumbnails displayed alongside the answer

**Independent Test**: Ask a question pulling from multiple pages, verify answer contains [1], [2] markers, and each marker maps to a visible numbered thumbnail

### Implementation for User Story 3

- [x] T007 [US3] Modify the VLM prompt construction in `generate_answer()` in `src/generate.py`: number each source page image in the prompt as `Source [1]: {filename} page {page_number}`, `Source [2]: ...`, etc. Add instruction text: "Cite your sources using numbered markers like [1], [2] when referencing information from the source pages. Only cite sources you actually use." Append each image content block with its corresponding source label. Return the generated answer text with inline [N] markers.
- [x] T008 [US3] Update the source display in `app.py`: after `handle_message()` receives retrieval results, build gallery items with citation-numbered captions: `"[1] {filename} p.{page_number} (score: {score:.3f})"`, `"[2] ..."`, etc. matching the numbering used in the VLM prompt. Display in the `gr.Gallery` below the chat. When generation is unavailable (fallback), still show source thumbnails without citation numbers. Ensure all retrieved pages appear in the gallery even if the answer only cites some of them.

**Checkpoint**: Answers contain [1], [2] markers. Source panel shows numbered thumbnails matching the citation numbers. User can cross-reference claims in the answer with source pages.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and edge case handling

- [x] T009 Run quickstart.md validation scenarios 1–7 end-to-end: upload and verify library (scenario 1), delete and verify removal (scenario 2), multi-turn conversation (scenario 3), clear chat (scenario 4), citation verification (scenario 5), empty state (scenario 6), generation service unavailable (scenario 7). Fix any issues found.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 2)**: Depends on Phase 1 completion (needs library.py)
- **US2 (Phase 3)**: Backend tasks T004, T005 can start after Phase 1 (different files). UI task T006 depends on T003 (needs new app.py layout), T004, and T005.
- **US3 (Phase 4)**: Depends on T005 (modifies same function in generate.py) and T006 (needs chat UI in app.py)
- **Polish (Phase 5)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependencies on other stories
- **US2 (P1)**: Backend (T004, T005) independent of US1. UI (T006) depends on US1 completing the app.py rewrite
- **US3 (P2)**: Depends on US2's generate.py changes (T005) and app.py chat UI (T006)

### Within Each User Story

- Backend/service functions before UI integration
- Core logic before wiring
- Each task builds on the previous within its story

### Parallel Opportunities

- T004 and T005 can run in parallel (different files: retrieve.py vs generate.py)
- T004 and T005 can also run in parallel with T003 (different files)
- T007 and T008 are sequential (T008 depends on the prompt numbering from T007)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (CRITICAL — blocks all stories)
2. Complete Phase 2: User Story 1 (Document Library)
3. **STOP and VALIDATE**: Upload documents, verify library display, delete, verify removal
4. Demo document management UX

### Full Feature

5. Complete Phase 3: User Story 2 (Multi-Turn Chat) — T004 + T005 in parallel, then T006
6. **STOP and VALIDATE**: Multi-turn conversation with follow-ups
7. Complete Phase 4: User Story 3 (Inline Citations)
8. **VALIDATE**: Citations map to source thumbnails
9. Complete Phase 5: Polish — run all quickstart scenarios

### Incremental Delivery

- After US1: "I can manage my document collection" (library demo)
- After US2: "I can have a research conversation" (chat demo)
- After US3: "I can verify every claim against sources" (full NotebookLM-style demo)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps each task to its user story for traceability
- app.py is built incrementally: US1 creates the layout, US2 adds chat, US3 adds citations
- No new dependencies required — all features use existing packages
- Conversation state is session-scoped via Gradio `gr.State` — lost on restart per FR-011
- Total: 9 tasks across 5 phases
