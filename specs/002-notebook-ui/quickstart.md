# Quickstart: NotebookLM-Style UI Validation

## Prerequisites

- Existing multimodal RAG POC is working (ingest, retrieve, generate)
- vLLM server running with Qwen3-VL-8B-Instruct
- Python environment with dependencies from `requirements.txt`
- At least one PDF document for testing

## Start the Application

```bash
VLLM_BASE_URL=http://localhost:8000/v1 python app.py
```

Open the browser at the displayed URL (default: `http://0.0.0.0:7860`).

## Scenario 1: Document Library — Upload and Verify

1. In the document library sidebar, observe the empty state message.
2. Upload a multi-page PDF using the upload button.
3. **Expected**: The library shows the document with filename and
   page count. Upload status confirms ingestion.
4. Upload a second document (image or PDF).
5. **Expected**: Both documents appear in the library with correct
   page counts.

## Scenario 2: Document Library — Delete

1. With two documents in the library, click the delete button next
   to the first document.
2. **Expected**: The document disappears from the library.
3. Ask a question that would have matched the deleted document.
4. **Expected**: Results come only from the remaining document. No
   pages from the deleted document appear.

## Scenario 3: Multi-Turn Chat — Basic Conversation

1. Type a question about an uploaded document and press Send.
2. **Expected**: The chat shows your question, then the assistant's
   answer with citation markers ([1], [2]).
3. Type a follow-up question that references the prior answer (e.g.,
   "Tell me more about that" or "What about the next section?").
4. **Expected**: The system returns a contextually relevant answer
   that resolves the reference to the prior exchange.

## Scenario 4: Multi-Turn Chat — Clear History

1. After a multi-turn conversation, click the Clear button.
2. **Expected**: The chat panel empties. The source panel clears.
3. Type a new question.
4. **Expected**: The system treats it as a fresh query with no prior
   context.

## Scenario 5: Inline Citations — Verification

1. Ask a question that requires information from multiple pages.
2. **Expected**: The answer contains numbered citation markers
   ([1], [2], etc.) inline with the text.
3. Look at the source panel below the chat.
4. **Expected**: Thumbnails are displayed with matching citation
   numbers, filenames, and page numbers.
5. Verify that each citation number in the answer corresponds to a
   visible thumbnail in the source panel.

## Scenario 6: Edge Case — No Documents

1. Start the application fresh (no documents uploaded).
2. Type a question in the chat.
3. **Expected**: The system displays a message indicating no
   documents are available. No crash or error.

## Scenario 7: Edge Case — Generation Service Unavailable

1. Upload a document.
2. Stop the vLLM server.
3. Ask a question.
4. **Expected**: Retrieved source pages are still displayed in the
   source panel. The answer area shows a fallback message indicating
   generation is unavailable.
