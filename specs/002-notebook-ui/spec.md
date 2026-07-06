# Feature Specification: NotebookLM-Style UI

**Feature Branch**: `feat/notebook-ui`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "Enhance the multimodal RAG PoC with a NotebookLM-style user experience. Add: (1) Document library panel showing all uploaded documents with filename, page count, and a delete button that removes that document's pages from Qdrant. (2) Multi-turn chat interface replacing the single-shot query box — conversation history maintained in session, follow-up questions resolve against prior context. (3) Inline source citations in generated answers — numbered references linking to retrieved page thumbnails displayed alongside the answer. Keep existing architecture (ColQwen2, Qdrant in-memory, Qwen3-VL via vLLM-Omni, Gradio). No persistence across restarts."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Document Library Management (Priority: P1)

A user has uploaded several documents and wants to see what is
currently available for search. They look at the document library
panel, which lists every uploaded document by filename and page
count. The user notices they uploaded the wrong version of a
report, so they click the delete button next to that document.
The system removes all of that document's pages from the search
index and updates the library view. The user then uploads the
correct version and confirms it appears in the library.

**Why this priority**: Users need visibility into and control over
their document collection before they can trust search results.
Without knowing what's ingested or being able to remove mistakes,
the system feels like a black box.

**Independent Test**: Upload three documents, verify all three
appear in the library with correct page counts, delete one,
verify it disappears from the library and its pages are no longer
returned in search results.

**Acceptance Scenarios**:

1. **Given** the user has uploaded 3 documents, **When** they view
   the document library, **Then** all 3 documents are listed with
   filename and page count.
2. **Given** a document is listed in the library, **When** the user
   clicks the delete button for that document, **Then** the document
   is removed from the library and its pages are no longer
   retrievable via search.
3. **Given** the user deletes a document and then uploads a new
   document, **Then** the library shows the remaining documents
   plus the newly uploaded one, with correct page counts.
4. **Given** no documents have been uploaded, **When** the user
   views the library, **Then** it displays an empty state message
   indicating no documents are available.

---

### User Story 2 - Multi-Turn Chat Interface (Priority: P1)

A user asks a question about their documents and receives an
answer with source pages. They want to follow up — "What about
the previous quarter?" or "Can you compare that to the budget?"
Instead of re-typing context, they type their follow-up directly
in the chat. The system understands the follow-up in the context
of the prior conversation, retrieves relevant pages, and
generates a contextually aware answer. The full conversation
history is visible in the chat panel.

**Why this priority**: Single-shot Q&A forces users to repeat
themselves and makes exploration tedious. Multi-turn conversation
is the core UX improvement that transforms the tool from a search
box into a research assistant.

**Independent Test**: Ask an initial question, then ask a follow-up
that uses a pronoun referencing the first answer (e.g., "Tell me
more about that"). Verify the system resolves the reference and
returns a relevant answer rather than treating it as a standalone
query.

**Acceptance Scenarios**:

1. **Given** a user asks an initial question and receives an answer,
   **When** they type a follow-up question referencing the prior
   exchange, **Then** the system produces an answer that accounts
   for the conversation history.
2. **Given** an ongoing conversation, **When** the user scrolls up,
   **Then** they can see the full history of questions and answers
   in the chat panel.
3. **Given** a multi-turn conversation, **When** the user starts a
   new conversation (clears chat), **Then** the conversation history
   is reset and follow-up context is cleared.
4. **Given** no documents are uploaded, **When** the user tries to
   ask a question, **Then** the system displays a message prompting
   them to upload documents first.

---

### User Story 3 - Inline Source Citations (Priority: P2)

After the system generates an answer, the user wants to know
which specific pages support each claim. The answer contains
numbered citation markers (e.g., [1], [2]) that correspond to
the retrieved source pages displayed alongside the answer. The
user can look at a citation number, find the matching thumbnail,
and verify the claim against the original page content.

**Why this priority**: Citations are the trust layer — they let
users verify answers without re-reading entire documents. This
depends on working retrieval and generation (US1 + US2) and
adds a polish layer that distinguishes a research tool from a
chatbot.

**Independent Test**: Ask a question that pulls from multiple
source pages. Verify the answer contains numbered citation
markers, and that each marker corresponds to a visible source
page thumbnail with matching filename and page number.

**Acceptance Scenarios**:

1. **Given** a generated answer that draws on multiple source pages,
   **When** the answer is displayed, **Then** it contains numbered
   citation markers (e.g., [1], [2]) inline with the text.
2. **Given** citation markers in an answer, **When** the user views
   the source panel, **Then** each citation number maps to a
   visible page thumbnail with filename and page number.
3. **Given** the system retrieves 5 source pages, **When** the
   answer references only 3 of them, **Then** only those 3 appear
   as numbered citations in the answer, while all 5 remain visible
   in the source panel.
4. **Given** the system cannot generate an answer (service
   unavailable), **When** results are displayed, **Then** the
   retrieved source pages are still shown without citations.

---

### Edge Cases

- What happens when the user deletes a document while a chat
  conversation references pages from that document? Previously
  generated answers remain visible in chat history, but subsequent
  queries will not retrieve deleted pages.
- What happens when a follow-up question has no meaningful
  connection to the prior conversation? The system treats it as a
  new search query — retrieval is always based on the full
  conversation context, which naturally handles topic shifts.
- What happens when the chat history becomes very long (50+
  exchanges)? The system MUST remain responsive. Only a bounded
  window of recent conversation history is sent for answer
  generation to avoid exceeding model input limits.
- What happens when a user uploads a document with the same
  filename as an existing one? Both versions are kept in the
  library as separate entries — the system treats each upload as
  a distinct document.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a document library panel showing
  all uploaded documents with filename and page count.
- **FR-002**: System MUST provide a delete action per document that
  removes all of that document's pages from the search index.
- **FR-003**: The document library MUST update immediately after
  upload or deletion without requiring a page refresh.
- **FR-004**: System MUST provide a multi-turn chat interface that
  replaces the existing single-shot query input.
- **FR-005**: System MUST maintain conversation history within the
  current session so follow-up questions can reference prior
  context.
- **FR-006**: System MUST include conversation history when
  generating answers so that follow-up questions are resolved
  against prior exchanges.
- **FR-007**: System MUST provide a way to clear conversation
  history and start a new chat.
- **FR-008**: System MUST include numbered citation markers in
  generated answers that correspond to specific source pages.
- **FR-009**: System MUST display source page thumbnails alongside
  the answer, labeled with citation numbers, filenames, and page
  numbers.
- **FR-010**: System MUST show all retrieved source pages in the
  source panel, even if not all are cited in the answer text.
- **FR-011**: Conversation history and document library state MUST
  NOT persist across application restarts.
- **FR-012**: System MUST remain functional when the answer
  generation service is unavailable — retrieval results and source
  pages are still displayed.

### Key Entities

- **Document Library Entry**: Represents an uploaded document in
  the library view. Has a document identifier, filename, and page
  count. Used for display and deletion.
- **Conversation**: An ordered sequence of user questions and
  system answers within a single session. Cleared on reset or
  application restart.
- **Chat Message**: A single exchange in a conversation — either
  a user question or a system answer. System answers include
  generated text and associated source citations.
- **Citation**: A numbered reference within a generated answer
  linking to a specific source page. Has a citation number,
  source filename, and page number.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see all uploaded documents with correct
  page counts within 1 second of the library panel loading.
- **SC-002**: After deleting a document, its pages no longer appear
  in any subsequent search results.
- **SC-003**: Follow-up questions that use pronouns or references
  to prior answers produce contextually relevant responses at
  least 70% of the time (judged by human evaluation).
- **SC-004**: Every generated answer that references source
  material includes at least one numbered citation marker linking
  to a visible source page.
- **SC-005**: A user can conduct a 5-turn conversation without
  needing to re-state context from earlier turns.

## Assumptions

- This builds on the existing multimodal RAG pipeline — document
  ingestion, embedding, retrieval, and answer generation already
  work end-to-end.
- Single-user, single-session usage. No concurrent users or shared
  state between sessions.
- Conversation history is bounded — a reasonable window of recent
  exchanges is used for context, not the entire unbounded history.
  A default of 10 most recent exchanges is assumed.
- The existing retrieval quality and answer generation capabilities
  are unchanged — this feature enhances the user experience layer,
  not the core pipeline.
- Duplicate filenames from separate uploads are treated as distinct
  documents.
- The answer generation service instructs the model to include
  citation markers — the quality of citation placement depends on
  the underlying model's capabilities.
