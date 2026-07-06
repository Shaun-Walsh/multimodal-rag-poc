# Research: NotebookLM-Style UI

## R1: Gradio Chat Component

**Decision**: Use `gr.Chatbot` with Blocks and manual event handlers.

**Rationale**: `gr.ChatInterface` is convenient for simple chatbots
but hides layout customization. We need a document library sidebar,
custom clear/reset button, and source thumbnails alongside answers —
all of which require Blocks-level control.

**Key findings**:
- Use `type='messages'` format on `gr.Chatbot`:
  `[{"role": "user"|"assistant", "content": "..."}]`
- Images in chat messages require saved file paths, not inline base64
- Layout: `gr.Row` with `gr.Column(scale=1)` for sidebar and
  `gr.Column(scale=3)` for chat area
- `gr.State` provides per-session state (conversation history)
- No global state shared between sessions (matches our constraint)

**Alternatives considered**:
- `gr.ChatInterface`: Too limited for sidebar layout and custom
  source panel
- `gr.Sidebar()` (Gradio 4.x): Collapsible sidebar component,
  viable but `Row`/`Column` layout is simpler and more portable

---

## R2: Multi-Turn Retrieval Strategy

**Decision**: Concatenate last 1–2 user messages with the current
query before embedding. Pass full conversation history to VLM for
generation context.

**Rationale**: ColQwen2 uses late-interaction (token-level)
embeddings, which are robust to multi-sentence query inputs. This
approach requires no extra API call, no additional latency, and
aligns with the POC-First Simplicity constitution principle.

**Implementation**: Format as
`"{previous_query} | {current_query}"` before passing to
`embed_query()`. Use the last 1 previous user message (expand to
2–3 if needed based on testing).

**Alternatives considered**:
- Raw query only: Simple but fails for pronoun references ("tell me
  more about that"). Rejected because SC-003 requires 70% follow-up
  success rate.
- VLM query reformulation: Best quality but adds 200–500ms per turn
  for an extra VLM call. Overkill for POC.
- History in generation only: Retrieval misses on follow-ups make
  generation unreliable even with full context.

---

## R3: Document Deletion from Qdrant

**Decision**: Use `client.delete()` with payload filter on `doc_id`.
Maintain an in-memory document registry dict alongside Qdrant.

**Rationale**: Qdrant has no native grouping or aggregation queries.
Scrolling all points to list documents is O(n) on total pages — too
slow for a responsive library panel. An in-memory dict updated during
ingest and delete operations provides O(1) lookups.

**Implementation**:
- Delete: `client.delete(collection_name, points_selector=FilterSelector(filter=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))])))`
- Registry: module-level `_document_registry: dict[str, dict]`
  mapping `doc_id → {filename, page_count}`, updated in
  `ingest_document()` and a new `delete_document()` function.

**Alternatives considered**:
- Scroll + aggregate on every list call: Works but O(n) per call,
  sluggish for 500+ page collections.
- Separate SQLite or file-based index: Overkill for in-memory POC
  with no persistence requirement.

---

## R4: Citation Prompt Engineering

**Decision**: Number source pages in the VLM prompt and instruct the
model to cite using `[1]`, `[2]` markers inline.

**Rationale**: VLMs like Qwen3-VL follow citation instructions
reliably when sources are explicitly numbered in the prompt. This is
the standard pattern used by Perplexity, ChatGPT with browsing, and
similar citation-generating systems.

**Implementation**: Provide each source page with a label like
`Source [1]: report.pdf page 3`, and add the instruction: "Cite your
sources using [N] markers." Display source thumbnails with matching
numbers alongside the answer.

**Alternatives considered**:
- Post-hoc citation extraction: Parse the answer for page references
  after generation. Fragile and error-prone.
- No citation markers (just show source pages): Fails FR-008 which
  requires numbered inline citations.

---

## R5: Chat Message Image Display

**Decision**: Save source page thumbnails as temporary files and
reference them by path in chat messages. Display as a numbered
source panel below each assistant message rather than inline images.

**Rationale**: Gradio's `gr.Chatbot` requires file paths for images
in messages (not inline base64). For the source citation panel, a
separate `gr.Gallery` or `gr.HTML` component per message turn is
cleaner than embedding multiple images directly in chat bubbles.

**Implementation**: After each answer, display the source thumbnails
in a dedicated panel below the chat, labeled with citation numbers.
This keeps the chat readable while providing visual verification.

**Alternatives considered**:
- Inline images in chat messages: Clutters the conversation flow,
  makes scrolling through history unwieldy.
- Persistent side panel: Would show sources for all turns at once,
  losing the per-answer association.
