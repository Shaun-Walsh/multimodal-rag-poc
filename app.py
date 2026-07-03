import gradio as gr

from src.generate import generate_answer
from src.ingest import ingest_document
from src.retrieve import retrieve


def handle_upload(files):
    if not files:
        return "No files selected."

    results = []
    total_pages = 0
    for f in files:
        file_path = f.name if hasattr(f, "name") else f
        try:
            n = ingest_document(file_path)
            total_pages += n
            results.append(f"  {file_path}: {n} page(s) ingested")
        except ValueError as e:
            results.append(f"  {file_path}: ERROR — {e}")

    summary = f"Ingested {total_pages} page(s) from {len(files)} file(s):\n"
    return summary + "\n".join(results)


def handle_query(query):
    if not query or not query.strip():
        return [], "Please enter a query.", ""

    results = retrieve(query.strip())

    if not results:
        return [], "", "No documents uploaded yet. Please upload documents first."

    gallery_items = []
    sources = []
    for r in results:
        caption = f"{r['filename']} p.{r['page_number']} (score: {r['score']:.3f})"
        if r["image"]:
            gallery_items.append((r["image"], caption))
        sources.append(f"- **{r['filename']}** page {r['page_number']} — score {r['score']:.3f}")

    source_text = "### Sources\n" + "\n".join(sources)

    answer = generate_answer(query.strip(), results)

    answer_text = f"### Answer\n\n{answer}\n\n{source_text}"
    return gallery_items, answer_text, ""


def build_app():
    with gr.Blocks(title="Multimodal RAG POC") as app:
        gr.Markdown("# Multimodal RAG POC")
        gr.Markdown(
            "Vision-based retrieval-augmented generation over "
            "documents, slides, and images."
        )

        with gr.Tab("Upload"):
            file_input = gr.File(
                file_count="multiple",
                file_types=[".pdf", ".png", ".jpg", ".jpeg"],
                label="Upload documents",
            )
            upload_btn = gr.Button("Ingest Documents")
            upload_status = gr.Textbox(label="Status", interactive=False)
            upload_btn.click(handle_upload, inputs=file_input, outputs=upload_status)

        with gr.Tab("Query"):
            query_input = gr.Textbox(
                label="Ask a question",
                placeholder="What does the document say about...?",
            )
            query_btn = gr.Button("Search")
            gallery = gr.Gallery(label="Retrieved Pages", columns=3, height="auto")
            answer_md = gr.Markdown(label="Answer")
            status_md = gr.Markdown()
            query_btn.click(
                handle_query,
                inputs=query_input,
                outputs=[gallery, answer_md, status_md],
            )

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0")
