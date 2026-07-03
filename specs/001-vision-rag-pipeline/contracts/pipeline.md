# Pipeline Contracts

## Ingestion Pipeline

### ingest_document(file_path: str) → list[PageImage]

Accepts a file path to a PDF or image. Returns a list of PageImage
objects, each containing the rendered image and its embeddings
stored in Qdrant.

**Input**: File path (PDF, PNG, JPG, JPEG)
**Output**: List of PageImage objects with populated embeddings
**Side effects**: Upserts multi-vector points into Qdrant

**Error cases**:
- Unsupported file type → raises ValueError with format message
- Corrupted/empty PDF → raises ValueError, skips file
- Embedding failure → raises RuntimeError

### render_pdf_pages(file_path: str) → list[PIL.Image]

Converts a PDF to a list of PIL Image objects (one per page) at
300 DPI using PyMuPDF.

**Input**: Path to PDF file
**Output**: List of PIL.Image.Image objects

### embed_images(images: list[PIL.Image]) → list[np.ndarray]

Embeds page images using ColQwen2. Returns multi-vector
embeddings for each image.

**Input**: List of PIL Image objects
**Output**: List of numpy arrays, each shape (N, 128) where N is
the number of patch vectors for that image

## Retrieval Pipeline

### retrieve(query: str, top_k: int = 5) → list[RetrievalResult]

Embeds the query text, performs MaxSim search in Qdrant, and
returns the top-k matching page images with scores.

**Input**: Natural language query string, number of results
**Output**: List of RetrievalResult (page image, score, metadata)

### embed_query(query: str) → np.ndarray

Embeds a text query using ColQwen2's query processor.

**Input**: Query text string
**Output**: numpy array of shape (T, 128) where T is number of
query tokens

## Generation Pipeline

### generate_answer(query: str, pages: list[RetrievalResult]) → str

Sends the query and retrieved page images to Qwen3-VL via the
vLLM OpenAI-compatible API. Returns the generated answer text.

**Input**: Query string, list of retrieved page results
**Output**: Generated answer string

**vLLM API contract** (OpenAI-compatible):
- Endpoint: `POST /v1/chat/completions`
- Model: `Qwen/Qwen3-VL-8B-Instruct`
- Messages format: user message with multiple `image_url` content
  blocks (base64-encoded JPEGs) followed by a text block with
  the query and instructions
- Response: standard chat completion with generated answer in
  `choices[0].message.content`

## Gradio UI

### Upload Tab

- File input: accepts multiple files (PDF, PNG, JPG, JPEG)
- Progress indicator during ingestion
- Status message on completion (files ingested, pages processed)

### Query Tab

- Text input for natural language question
- Gallery display for top-k retrieved page images with scores
- Markdown display for generated answer
- Source attribution (filename + page number) per result
