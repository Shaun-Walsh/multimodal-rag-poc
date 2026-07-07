# Multimodal RAG POC

A proof of concept for vision-native retrieval-augmented generation over documents. Upload PDFs, slides, or images, ask questions, and get answers grounded in the visual content of your pages — no OCR required.

## How It Works

Traditional RAG pipelines extract text from documents before embedding it. This system skips text extraction entirely: document pages are rendered as images, embedded using [ColPali](https://arxiv.org/abs/2407.01449) late-interaction embeddings (ColQwen2), and retrieved via Qdrant's MaxSim multi-vector search. A vision-language model (Qwen3-VL) then reads the retrieved page images directly to generate answers.

This means charts, diagrams, tables, handwritten notes, and complex layouts are all searchable and usable for answer generation — anything the VLM can see.

```
PDF/Image ─► Render pages ─► ColQwen2 embed ─► Qdrant (in-memory)
                                                      │
User query ─► ColQwen2 embed ─► MaxSim search ────────┘
                                      │
                              Top-K page images ─► Qwen3-VL (vLLM) ─► Answer
```

## Prerequisites

- Python 3.10+
- CUDA-capable GPU (ColQwen2 runs locally)
- [vLLM](https://docs.vllm.ai/) serving Qwen3-VL-8B-Instruct

Start the vLLM server:

```bash
vllm serve Qwen/Qwen3-VL-8B-Instruct
```

## Setup

```bash
git clone <repo-url>
cd multimodal-rag-poc
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
VLLM_BASE_URL=http://localhost:8000/v1 python app.py
```

Open `http://localhost:7860` in your browser.

1. **Upload tab** — Upload PDFs or images. Each page is embedded and indexed.
2. **Query tab** — Ask a question. The system retrieves the most relevant pages and generates an answer using the VLM.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_BASE_URL` | `http://localhost:8000/v1` | vLLM OpenAI-compatible endpoint |

Constants in `src/config.py`:

| Constant | Value | Description |
|----------|-------|-------------|
| `COLQWEN2_MODEL_NAME` | `vidore/colqwen2-v1.0` | ColPali embedding model |
| `QWEN3_VL_MODEL_NAME` | `Qwen/Qwen3-VL-8B-Instruct` | Vision-language model for generation |
| `DEFAULT_TOP_K` | `5` | Number of pages retrieved per query |
| `EMBEDDING_DIM` | `128` | ColQwen2 multi-vector embedding dimension |

## Evaluation

A retrieval quality evaluation harness is included under `eval/`.

1. Place test documents in a directory
2. Edit `eval/queries.json` with queries and expected document/page pairs
3. Run:

```bash
python -m eval.evaluate <docs_directory>
```

Reports Recall@5 and MRR against a configurable target (default 80% recall).

## Project Structure

```
app.py              # Gradio UI — upload and query tabs
src/
  config.py         # Model names, Qdrant setup, shared constants
  ingest.py         # PDF rendering, ColQwen2 embedding, Qdrant upsert
  retrieve.py       # Query embedding, MaxSim search
  generate.py       # vLLM/Qwen3-VL answer generation
eval/
  evaluate.py       # Retrieval quality evaluation (Recall@K, MRR)
  queries.json      # Evaluation dataset template
```

## Limitations

- **No persistence** — The vector index is in-memory (Qdrant `:memory:` mode); everything resets on restart
- **Single user** — No concurrent session support; designed for local experimentation
- **GPU required** — ColQwen2 embedding model needs a CUDA GPU
