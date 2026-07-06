import base64
import io

import numpy as np
import torch
from PIL import Image

from src.config import (
    DEFAULT_TOP_K,
    QDRANT_COLLECTION_NAME,
    get_model,
    get_qdrant_client,
)


def build_contextualized_query(query: str, history: list[dict]) -> str:
    """Prepend up to the last 2 user messages from history to the current query.

    This gives the retrieval embedding richer context when the user asks
    follow-up questions that rely on earlier turns (e.g. "Compare to Q2"
    after discussing Q3 revenue).
    """
    prior_user_msgs = [m["content"] for m in history if m.get("role") == "user"]
    if not prior_user_msgs:
        return query
    recent = prior_user_msgs[-2:]  # last 2 user messages
    return " | ".join(recent + [query])


def embed_query(query: str) -> np.ndarray:
    model, processor = get_model()
    batch = processor.process_queries([query])
    batch = {k: v.to(model.device) for k, v in batch.items()}

    with torch.no_grad():
        embeddings = model(**batch)

    return embeddings[0].cpu().float().numpy()


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    client = get_qdrant_client()

    collection_info = client.get_collection(QDRANT_COLLECTION_NAME)
    if collection_info.points_count == 0:
        return []

    query_embedding = embed_query(query)

    results = client.query_points(
        collection_name=QDRANT_COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=top_k,
        using="colpali",
        with_payload=True,
    )

    retrieved = []
    for point in results.points:
        img_b64 = point.payload.get("image_b64", "")
        img = Image.open(io.BytesIO(base64.b64decode(img_b64))) if img_b64 else None

        retrieved.append(
            {
                "page_id": str(point.id),
                "doc_id": point.payload.get("doc_id", ""),
                "filename": point.payload.get("filename", ""),
                "page_number": point.payload.get("page_number", 0),
                "score": point.score,
                "image": img,
            }
        )

    return retrieved
