# Research: Vision-Based Multimodal RAG Pipeline

## R1. ColPali/ColQwen2 Embedding Model

**Decision**: Use `vidore/colqwen2-v1.0` via the `colpali-engine` package.

**Rationale**: ColQwen2 supports arbitrary image resolutions and aspect
ratios (unlike ColPali which resizes to fixed squares), preserving
more visual signal from document pages. It produces up to 768 patch
vectors of 128 dimensions per image using late interaction (MaxSim).
Query text is tokenized into the same 128-d space, enabling
cross-modal retrieval without OCR.

**Alternatives considered**:
- `vidore/colpali` (original): Fixed 32x32 grid = 1030 vectors per
  image. Slightly more storage per page but works. ColQwen2 chosen
  for better resolution handling.
- `vidore/colqwen2.5-v0.2` (newer): Could be used as a drop-in
  replacement if retrieval quality is higher; same API.

**Key details**:
- Install: `pip install colpali-engine`
- Embedding dimension: 128
- Vectors per page: up to 768 (ColQwen2) or 1030 (ColPali)
- GPU: works on 16GB T4 or Apple MPS with bfloat16
- Query and document embeddings share the same latent space
- Scoring: MaxSim (each query token finds best match among all
  document patch vectors)

## R2. Qdrant Multi-Vector Storage

**Decision**: Use Qdrant in embedded/in-memory mode with native
multi-vector support and MaxSim comparator.

**Rationale**: Qdrant natively supports multi-vector points with
MaxSim scoring — no need to flatten patch vectors or compute scores
client-side. In-memory mode eliminates server setup for the POC.

**Alternatives considered**:
- Vespa: Strong ColPali support but heavier infra setup.
- Weaviate: Multi-vector support available but Qdrant has the most
  documented ColPali integration path.
- Manual numpy-based MaxSim: Would work for small collections but
  Qdrant handles indexing and scales better even for POC sizes.

**Key details**:
- Install: `pip install qdrant-client`
- In-memory: `QdrantClient(":memory:")`
- Persistent: `QdrantClient(path="./qdrant_storage")`
- Collection config: `MultiVectorConfig(comparator=MAX_SIM)`,
  distance=COSINE, size=128, HNSW m=0 (brute-force for POC)

## R3. vLLM with Qwen3-VL for Answer Generation

**Decision**: Serve `Qwen/Qwen3-VL-8B-Instruct` via vLLM (>=0.11.0)
using its OpenAI-compatible API. Fall back to 4B variant if GPU
memory is constrained.

**Rationale**: Qwen3-VL is a strong vision-language model that
accepts multiple images per request, which is essential for passing
top-k retrieved pages alongside the query. vLLM provides an
OpenAI-compatible serving layer with efficient batching.

**Alternatives considered**:
- Qwen3-VL-4B-Instruct: ~12GB VRAM FP16. Use if 8B is too large.
- Qwen3-VL-2B-Instruct: Smallest variant, but answer quality may
  suffer for complex documents.
- Qwen2.5-VL: Previous generation, well-tested with vLLM. Fallback
  if Qwen3-VL has compatibility issues.
- Direct transformers inference (no vLLM): Simpler but no concurrent
  request support and slower for repeated queries.

**Key details**:
- Model: `Qwen/Qwen3-VL-8B-Instruct` (~20GB VRAM FP16)
- vLLM version: >= 0.11.0
- Multi-image: pass multiple `image_url` content blocks in messages
- Base64 format: `data:image/jpeg;base64,{encoded}`
- Server: `vllm serve Qwen/Qwen3-VL-8B-Instruct`
- Limit: `--limit-mm-per-prompt image=5` (configurable top-k)

## R4. PDF-to-Image Conversion

**Decision**: Use PyMuPDF (fitz) for PDF page rendering.

**Rationale**: Pure Python wheels (no system dependencies like
poppler), fast C-backed rendering, straightforward DPI control.
Minimal setup friction for a 3-day POC.

**Alternatives considered**:
- pdf2image (poppler): Simple API but requires system-level poppler
  installation.
- pypdfium2: Good alternative, Google's PDFium backend. Would also
  work.

**Key details**:
- Install: `pip install pymupdf Pillow`
- Render at 300 DPI (standard for ColPali): matrix scale = 300/72
- Output: PIL Image objects, one per page

## R5. Gradio UI

**Decision**: Use Gradio for the upload and query interface.

**Rationale**: Specified in requirements. Gradio provides file upload,
text input, image display, and text output components with minimal
code. Ideal for a POC demo interface.

**Key details**:
- Install: `pip install gradio`
- File upload: `gr.File(file_count="multiple")`
- Query input: `gr.Textbox`
- Results display: `gr.Gallery` for page images + `gr.Markdown`
  for generated answer
