# Multimodal RAG POC

A vision-native retrieval-augmented generation proof of concept. Upload PDFs or images, ask questions in a multi-turn chat, and get answers grounded in your documents with inline source citations.

Unlike traditional RAG pipelines that extract text via OCR, this system embeds document pages as images using [ColPali](https://arxiv.org/abs/2407.01449) (ColQwen2) late-interaction embeddings and retrieves them with Qdrant's MaxSim multi-vector search. A vision-language model (Qwen3-VL) reads the retrieved page images directly to generate answers.

## Architecture

```
PDF/Image ─► Render pages ─► ColQwen2 embed ─► Qdrant (in-memory)
                                                      │
User query ─► ColQwen2 embed ─► MaxSim search ────────┘
                                      │
                              Top-K page images ─► Qwen3-VL (vLLM) ─► Answer with [1][2] citations
```

**Stack**: Python, Gradio, ColQwen2 (colpali-engine), Qdrant, vLLM + Qwen3-VL-8B-Instruct

## Features

- **Document library** — Upload PDFs and images, see page counts, delete documents from the index
- **Multi-turn chat** — Follow-up questions resolve against conversation history
- **Inline citations** — Answers include numbered markers ([1], [2]) mapped to source page thumbnails
- **Vision-native retrieval** — No OCR; pages are embedded and retrieved as images

## Prerequisites

- Python 3.10+
- CUDA-capable GPU (ColQwen2 embedding model runs locally)
- [vLLM](https://docs.vllm.ai/) serving Qwen3-VL-8B-Instruct

### Start the vLLM server

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

1. Upload documents in the sidebar (PDF, PNG, JPG)
2. Ask questions in the chat panel
3. View source page thumbnails with citation numbers below the chat
4. Use "Clear Chat" to reset conversation context

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
app.py              # Gradio UI — chat, document library, source gallery
src/
  config.py         # Model names, Qdrant setup, shared constants
  ingest.py         # PDF rendering, ColQwen2 embedding, Qdrant upsert
  retrieve.py       # Query embedding, MaxSim search, context builder
  generate.py       # vLLM/Qwen3-VL answer generation with citations
  library.py        # In-memory document registry (list, delete)
eval/
  evaluate.py       # Retrieval quality evaluation (Recall@K, MRR)
  queries.json      # Evaluation dataset template
```

## Limitations

- **No persistence** — Document index and chat history are in-memory; everything resets on restart
- **Single user** — No concurrent session support; designed for local single-user experimentation
- **GPU required** — ColQwen2 embedding model needs a CUDA GPU
