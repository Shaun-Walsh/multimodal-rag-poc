# Quickstart: Vision-Based Multimodal RAG Pipeline

## Prerequisites

- Python >= 3.10
- GPU with >= 20GB VRAM for Qwen3-VL-8B (or >= 12GB for 4B)
- CUDA toolkit installed
- ~10GB disk for model weights (ColQwen2 + Qwen3-VL cached by
  HuggingFace)

## Setup

```bash
# Clone and enter project
cd multimodal-rag-poc

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install colpali-engine qdrant-client pymupdf Pillow gradio openai torch

# Install vLLM (separate due to CUDA dependency)
pip install vllm>=0.11.0
```

## Start vLLM Server

In a separate terminal:

```bash
vllm serve Qwen/Qwen3-VL-8B-Instruct \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --limit-mm-per-prompt.image 5 \
  --port 8000
```

Wait for "Uvicorn running on..." before proceeding.

## Run the Application

```bash
python app.py
```

Open the URL printed by Gradio (typically http://localhost:7860).

## Validation Scenarios

### Scenario 1: Single PDF Upload + Query

1. Open the Gradio UI
2. Upload `test_data/sample_report.pdf` (a PDF with known content)
3. Wait for ingestion confirmation
4. Enter query: "What is the main conclusion?"
5. **Expected**: Retrieved pages contain the conclusion section;
   generated answer references visible content from those pages

### Scenario 2: Mixed Upload (PDF + Images)

1. Upload a PDF and two standalone images
2. Query about content specific to one of the images
3. **Expected**: The relevant image appears in top results
   alongside PDF pages, ranked by relevance

### Scenario 3: Retrieval Quality Check

1. Upload a multi-page document with distinct content per page
2. Ask a question whose answer is on a specific page
3. **Expected**: That page appears in the top 5 results

### Scenario 4: No Documents Uploaded

1. Without uploading anything, submit a query
2. **Expected**: System displays a message indicating no documents
   are available

### Scenario 5: Unsupported File Type

1. Attempt to upload a .docx or .mp4 file
2. **Expected**: System rejects the file with a clear error message

## Troubleshooting

- **vLLM OOM**: Use the 4B model variant:
  `vllm serve Qwen/Qwen3-VL-4B-Instruct --dtype bfloat16 ...`
- **ColQwen2 OOM**: Reduce batch size in embedding code to 1
- **Slow PDF rendering**: Normal for 100+ page PDFs at 300 DPI
- **Qdrant errors**: Ensure `qdrant-client` is >= 1.7.0 for
  multi-vector support
