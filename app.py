import gradio as gr

from src.generate import generate_answer
from src.ingest import ingest_document
from src.library import delete_document, list_documents
from src.retrieve import build_contextualized_query, retrieve


def render_library_html():
    docs = list_documents()
    if not docs:
        return "<p style='color: #888; text-align: center;'>No documents uploaded yet.</p>"

    rows = []
    for doc in docs:
        rows.append(
            f"<tr>"
            f"<td style='padding:4px;'>{doc['filename']}</td>"
            f"<td style='text-align:center; padding:4px;'>{doc['page_count']}</td>"
            f"</tr>"
        )
    return (
        "<table style='width:100%; border-collapse:collapse; font-size:0.9em;'>"
        "<thead><tr>"
        "<th style='text-align:left; border-bottom:1px solid #ddd; padding:4px;'>File</th>"
        "<th style='text-align:center; border-bottom:1px solid #ddd; padding:4px;'>Pages</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def get_delete_choices():
    docs = list_documents()
    return [(f"{d['filename']} ({d['page_count']} pp)", d["doc_id"]) for d in docs]


def handle_upload(files):
    if not files:
        return render_library_html(), gr.update(choices=get_delete_choices()), "No files selected."

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
    return render_library_html(), gr.update(choices=get_delete_choices()), summary + "\n".join(results)


def handle_delete(doc_id):
    if not doc_id:
        return render_library_html(), gr.update(choices=get_delete_choices(), value=None), ""
    deleted = delete_document(doc_id)
    status = "Document deleted." if deleted else "Document not found."
    return render_library_html(), gr.update(choices=get_delete_choices(), value=None), status


def handle_message(query, history, chatbot_messages):
    if not query or not query.strip():
        return chatbot_messages, [], history, ""

    query = query.strip()
    docs = list_documents()
    if not docs:
        no_docs_msg = "Please upload documents first."
        updated_chatbot = chatbot_messages + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": no_docs_msg},
        ]
        updated_history = history + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": no_docs_msg},
        ]
        return updated_chatbot, [], updated_history, ""

    ctx_query = build_contextualized_query(query, history)
    results = retrieve(ctx_query)

    gallery_items = []
    for i, r in enumerate(results):
        citation_num = i + 1
        caption = f"[{citation_num}] {r['filename']} p.{r['page_number']} (score: {r['score']:.3f})"
        if r["image"]:
            gallery_items.append((r["image"], caption))

    answer = generate_answer(query, results, history=history)

    updated_history = history + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": answer},
    ]
    updated_chatbot = chatbot_messages + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": answer},
    ]

    return updated_chatbot, gallery_items, updated_history, ""


def handle_clear():
    return [], [], [], ""


def build_app():
    with gr.Blocks(title="Multimodal RAG — NotebookLM-Style") as app:
        gr.Markdown("# Multimodal RAG — NotebookLM-Style")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Document Library")
                library_html = gr.HTML(value=render_library_html())
                file_input = gr.File(
                    file_count="multiple",
                    file_types=[".pdf", ".png", ".jpg", ".jpeg"],
                    label="Upload documents",
                )
                upload_btn = gr.Button("Ingest Documents", variant="primary")
                upload_status = gr.Textbox(label="Status", interactive=False)

                delete_dropdown = gr.Dropdown(
                    choices=get_delete_choices(),
                    label="Select document to delete",
                    interactive=True,
                )
                delete_btn = gr.Button("Delete Selected", variant="stop")

                upload_btn.click(
                    handle_upload,
                    inputs=file_input,
                    outputs=[library_html, delete_dropdown, upload_status],
                )
                delete_btn.click(
                    handle_delete,
                    inputs=delete_dropdown,
                    outputs=[library_html, delete_dropdown, upload_status],
                )

            with gr.Column(scale=3):
                conversation_history = gr.State(value=[])

                chatbot = gr.Chatbot(
                    label="Chat",
                    height=500,
                )

                sources_gallery = gr.Gallery(
                    label="Source Pages",
                    columns=5,
                    height="auto",
                )

                with gr.Row():
                    query_input = gr.Textbox(
                        placeholder="Ask a question about your documents...",
                        show_label=False,
                        scale=4,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                    clear_btn = gr.Button("Clear Chat", scale=1)

                send_btn.click(
                    handle_message,
                    inputs=[query_input, conversation_history, chatbot],
                    outputs=[chatbot, sources_gallery, conversation_history, query_input],
                )
                query_input.submit(
                    handle_message,
                    inputs=[query_input, conversation_history, chatbot],
                    outputs=[chatbot, sources_gallery, conversation_history, query_input],
                )
                clear_btn.click(
                    handle_clear,
                    outputs=[chatbot, sources_gallery, conversation_history, query_input],
                )

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0")
