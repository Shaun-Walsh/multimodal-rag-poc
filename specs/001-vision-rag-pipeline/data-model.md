# Data Model: Vision-Based Multimodal RAG Pipeline

## Entities

### Document

Represents a user-uploaded file.

| Field          | Type     | Description                            |
|----------------|----------|----------------------------------------|
| doc_id         | str      | Unique identifier (UUID)               |
| filename       | str      | Original filename                      |
| file_type      | str      | "pdf" or "image" (png/jpg/jpeg)        |
| num_pages      | int      | Number of pages (1 for images)         |
| uploaded_at    | datetime | Upload timestamp                       |

### PageImage

A single page rendered as an image, the atomic unit for embedding
and retrieval.

| Field          | Type         | Description                         |
|----------------|--------------|-------------------------------------|
| page_id        | str          | Unique identifier (UUID)            |
| doc_id         | str          | Parent document reference           |
| page_number    | int          | 1-indexed page number               |
| image          | PIL.Image    | Rendered page image (in memory)     |
| embeddings     | list[float]  | Multi-vector embeddings (N x 128)   |

**Relationships**: PageImage belongs to one Document. A Document has
one or more PageImages.

**Storage**: PageImage embeddings are stored as multi-vector points
in Qdrant. The page image bytes are stored as payload metadata
(base64-encoded JPEG) alongside the vectors for retrieval display.

### Qdrant Point Schema

Each Qdrant point represents one PageImage:

| Field               | Qdrant Type    | Description                   |
|---------------------|----------------|-------------------------------|
| id                  | int/str        | Point ID (page_id)            |
| vectors["colpali"]  | multi-vector   | N x 128 patch embeddings      |
| payload.doc_id      | str            | Parent document ID            |
| payload.filename    | str            | Source filename                |
| payload.page_number | int            | Page number in document       |
| payload.image_b64   | str            | Base64-encoded page JPEG      |

### Query (runtime, not persisted)

| Field          | Type         | Description                         |
|----------------|--------------|-------------------------------------|
| text           | str          | Natural language question           |
| embeddings     | list[float]  | Multi-vector query embeddings       |
| top_k          | int          | Number of results to retrieve       |

### RetrievalResult (runtime, not persisted)

| Field          | Type         | Description                         |
|----------------|--------------|-------------------------------------|
| page_id        | str          | Matched page identifier             |
| doc_id         | str          | Parent document ID                  |
| filename       | str          | Source filename                      |
| page_number    | int          | Page number                         |
| score          | float        | MaxSim similarity score             |
| image          | PIL.Image    | Page image for display/generation   |

### GeneratedAnswer (runtime, not persisted)

| Field          | Type                | Description                  |
|----------------|---------------------|------------------------------|
| text           | str                 | Generated answer text        |
| source_pages   | list[RetrievalResult] | Pages used for generation  |

## State Transitions

```
Document upload → PDF/image validation → Page rendering →
  Embedding → Qdrant upsert → Ready for retrieval

Query input → Query embedding → Qdrant MaxSim search →
  Top-k retrieval → VLM generation → Answer + sources displayed
```

## Validation Rules

- file_type MUST be one of: pdf, png, jpg, jpeg
- num_pages MUST be >= 1
- page_number MUST be >= 1 and <= num_pages
- top_k MUST be >= 1 (default: 5)
- embeddings MUST have dimension 128 per vector
