import base64
import io

from PIL import Image
from openai import OpenAI

from src.config import QWEN3_VL_MODEL_NAME, VLLM_BASE_URL

MAX_GENERATION_EDGE = 768
JPEG_QUALITY = 75


def _resize_for_generation(img: Image.Image, max_edge: int = MAX_GENERATION_EDGE) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_edge:
        return img
    scale = max_edge / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def _page_image_to_data_uri(page: dict) -> str:
    if page.get("image"):
        img = _resize_for_generation(page["image"])
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    if page.get("image_b64"):
        raw = base64.b64decode(page["image_b64"])
        img = _resize_for_generation(Image.open(io.BytesIO(raw)))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    return ""


def generate_answer(query: str, pages: list[dict]) -> str:
    client = OpenAI(api_key="EMPTY", base_url=VLLM_BASE_URL)

    content = []
    for page in pages:
        data_uri = _page_image_to_data_uri(page)
        if data_uri:
            content.append(
                {"type": "image_url", "image_url": {"url": data_uri}}
            )

    source_refs = ", ".join(
        f"{p['filename']} p.{p['page_number']}" for p in pages
    )
    content.append(
        {
            "type": "text",
            "text": (
                f"Based on the document pages shown above, answer the "
                f"following question. Ground your answer in the visible "
                f"content of these pages. If the pages do not contain "
                f"enough information to answer, say so.\n\n"
                f"Question: {query}\n\n"
                f"Source pages: {source_refs}"
            ),
        }
    )

    try:
        response = client.chat.completions.create(
            model=QWEN3_VL_MODEL_NAME,
            messages=[{"role": "user", "content": content}],
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Generation unavailable: {e}]"
