# UI & Function Contracts

## Document Library

### list_documents() → list[dict]

Returns all documents currently in the registry.

**Output**: List of dicts with keys: `doc_id` (str), `filename`
(str), `page_count` (int). Empty list if no documents uploaded.

### delete_document(doc_id: str) → bool

Removes all pages for a document from Qdrant and the registry.

**Input**: Document identifier (UUID string)
**Output**: True if document was found and deleted, False if doc_id
not in registry.
**Side effects**: Deletes matching Qdrant points, removes registry
entry.

### register_document(doc_id: str, filename: str, page_count: int) → None

Adds a document to the registry after successful ingestion.

**Input**: Document metadata from ingest pipeline
**Side effects**: Updates the in-memory registry

## Multi-Turn Chat

### build_contextualized_query(query: str, history: list[dict]) → str

Builds a retrieval query that includes context from prior
conversation turns.

**Input**: Current user query, conversation history (list of
`{"role": str, "content": str}` dicts)
**Output**: Contextualized query string. If history is empty or has
only 1 turn, returns the raw query unchanged. Otherwise prepends
the last user message(s) separated by ` | `.

### generate_answer(query: str, pages: list[dict], history: list[dict] | None) → str

Extended to accept conversation history and produce cited answers.

**Input**:
- `query`: Current user question
- `pages`: Retrieved page results (same format as existing)
- `history`: Conversation history (last 10 exchanges max), or None
  for single-turn mode

**Output**: Generated answer text with inline citation markers
([1], [2], etc.) referencing the numbered source pages.

**Prompt structure**:
1. System-level instruction: answer using sources, cite with [N]
2. Conversation history (if any): prior user/assistant exchanges
3. Source pages: numbered `Source [1]: filename p.N`, etc. with
   base64 images
4. Current question

**Error handling**: If vLLM is unavailable, returns fallback message
(same as existing behavior).

## Gradio UI Layout

### Layout Structure

```
┌────────────────────────────────────────────────────┐
│  Multimodal RAG — NotebookLM-Style                 │
├──────────────┬─────────────────────────────────────┤
│              │                                     │
│  DOCUMENT    │           CHAT PANEL                │
│  LIBRARY     │                                     │
│              │  ┌─────────────────────────────┐    │
│  ┌────────┐  │  │  User: What are Q3 figures? │    │
│  │ doc.pdf│  │  │                             │    │
│  │ 10 pp  │  │  │  Assistant: Based on [1]... │    │
│  │  [X]   │  │  │                             │    │
│  ├────────┤  │  │  User: Compare to Q2?       │    │
│  │ img.png│  │  │                             │    │
│  │ 1 pp   │  │  │  Assistant: According to... │    │
│  │  [X]   │  │  └─────────────────────────────┘    │
│  └────────┘  │                                     │
│              │  ┌─────────────────────────────┐    │
│  [Upload]    │  │ Sources: [1] doc.pdf p.5    │    │
│              │  │          [2] doc.pdf p.8    │    │
│              │  └─────────────────────────────┘    │
│              │                                     │
│              │  ┌──────────────────────┐ [Send]    │
│              │  │ Type your question...│ [Clear]   │
│              │  └──────────────────────┘           │
├──────────────┴─────────────────────────────────────┤
│  Status bar                                        │
└────────────────────────────────────────────────────┘
```

### Component Mapping

| Area | Component | Purpose |
|------|-----------|---------|
| Document Library | `gr.Column(scale=1)` | Left sidebar |
| Library list | `gr.Dataframe` or `gr.HTML` | Document list with delete |
| Upload | `gr.File` + `gr.Button` | File upload (existing) |
| Chat panel | `gr.Column(scale=3)` | Main content area |
| Chat history | `gr.Chatbot(type='messages')` | Conversation display |
| Sources | `gr.Gallery` or `gr.HTML` | Numbered citation thumbnails |
| Input | `gr.Textbox` + `gr.Button` | Query input + send |
| Clear | `gr.Button` | Reset conversation |
| State | `gr.State` | Conversation history (session) |

### Event Wiring

| Trigger | Handler | Inputs | Outputs |
|---------|---------|--------|---------|
| Upload button | `handle_upload()` | files | library display, status |
| Delete button | `handle_delete()` | doc_id | library display, status |
| Send button | `handle_message()` | query, history, chatbot | chatbot, sources, history |
| Clear button | `handle_clear()` | — | chatbot, sources, history |
