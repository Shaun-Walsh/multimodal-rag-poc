import base64
import io
import os
import uuid

import numpy as np
import pymupdf
import torch
from PIL import Image
from qdrant_client import models

from src.config import (
    QDRANT_COLLECTION_NAME,
    SUPPORTED_EXTENSIONS,
    get_model,
    get_qdrant_client,
)

DPI_SCALE = 300 / 72


def render_pdf_pages(file_path: str) -> list[Image.Image]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in {".png", ".jpg", ".jpeg"}:
        return [Image.open(file_path).convert("RGB")]

    doc = pymupdf.open(file_path)
    if len(doc) == 0:
        raise ValueError(f"PDF has no pages: {file_path}")

    mat = pymupdf.Matrix(DPI_SCALE, DPI_SCALE)
    images = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images


def embed_images(images: list[Image.Image]) -> list[np.ndarray]:
    model, processor = get_model()
    batch = processor.process_images(images)
    batch = {k: v.to(model.device) for k, v in batch.items()}

    with torch.no_grad():
        embeddings = model(**batch)

    return [e.cpu().float().numpy() for e in embeddings]


def _image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def ingest_document(file_path: str) -> int:
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    images = render_pdf_pages(file_path)
    embeddings = embed_images(images)

    client = get_qdrant_client()
    doc_id = str(uuid.uuid4())
    filename = os.path.basename(file_path)

    points = []
    for i, (img, emb) in enumerate(zip(images, embeddings)):
        page_id = str(uuid.uuid4())
        points.append(
            models.PointStruct(
                id=page_id,
                vectors={"colpali": emb.tolist()},
                payload={
                    "doc_id": doc_id,
                    "filename": filename,
                    "page_number": i + 1,
                    "image_b64": _image_to_base64(img),
                },
            )
        )

    client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)
    return len(points)
