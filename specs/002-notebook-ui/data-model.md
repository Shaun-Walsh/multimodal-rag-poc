# Data Model: NotebookLM-Style UI

## New Entities

### DocumentRegistryEntry (in-memory, not persisted)

Tracks uploaded documents for the library panel. Maintained as a
module-level dict keyed by doc_id.

| Field       | Type | Description                              |
|-------------|------|------------------------------------------|
| doc_id      | str  | Unique identifier (UUID, from ingest)    |
| filename    | str  | Original filename                        |
| page_count  | int  | Number of pages ingested                 |

**Lifecycle**: Created when `ingest_document()` completes. Removed
when `delete_document()` is called. Lost on application restart.

### ChatMessage (in-memory, session-scoped)

A single message in the conversation. Stored in Gradio `gr.State`
as a list of dicts.

| Field       | Type        | Description                         |
|-------------|-------------|-------------------------------------|
| role        | str         | "user" or "assistant"               |
| content     | str         | Message text                        |

**Note**: Assistant messages contain the generated answer text with
inline citation markers ([1], [2], etc.). Source page data is not
stored in the message itself — it is displayed via the source panel.

### ConversationState (in-memory, session-scoped)

Holds the full session state for a single user. Maintained in
Gradio `gr.State`.

| Field          | Type             | Description                    |
|----------------|------------------|--------------------------------|
| messages       | list[ChatMessage]| Ordered conversation history   |
| source_pages   | list[SourceRef]  | Sources for the latest answer  |

### SourceRef (runtime, per-answer)

A numbered citation reference linking a generated answer claim to a
retrieved page.

| Field          | Type        | Description                        |
|----------------|-------------|------------------------------------|
| citation_num   | int         | 1-indexed citation number          |
| doc_id         | str         | Parent document identifier         |
| filename       | str         | Source filename                    |
| page_number    | int         | Page number in source document     |
| score          | float       | Retrieval similarity score         |
| image          | PIL.Image   | Page thumbnail for display         |

## Existing Entities (unchanged)

The following entities from the original data model are unchanged:

- **Qdrant Point Schema**: Same payload structure (doc_id, filename,
  page_number, image_b64) with colpali multi-vectors.
- **Query / RetrievalResult**: Same retrieval pipeline. The
  `retrieve()` function still returns the same dict structure.

## State Transitions

```
Document upload → ingest_document() → register in library
  → Library panel updates

Delete button click → delete_document(doc_id)
  → Remove from Qdrant + Remove from registry
  → Library panel updates

User types message → build contextualized query
  → retrieve() → generate_answer() with history + citations
  → Append user msg + assistant msg to conversation state
  → Update chat display + source panel

Clear chat → Reset conversation state
  → Empty chat display + source panel
```

## Validation Rules

- doc_id in delete requests MUST exist in the registry (no-op if
  not found)
- Conversation history passed to generation MUST be bounded to the
  last 10 exchanges (20 messages)
- Citation numbers MUST be sequential starting at 1, matching the
  order of source pages provided to the VLM
