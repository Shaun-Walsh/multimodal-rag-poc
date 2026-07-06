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


def generate_answer(query: str, pages: list[dict], history: list[dict] | None = None) -> str:
    client = OpenAI(api_key="EMPTY", base_url=VLLM_BASE_URL)

    content = []
    for i, page in enumerate(pages):
        citation_num = i + 1
        data_uri = _page_image_to_data_uri(page)
        if data_uri:
            content.append(
                {"type": "text", "text": f"Source [{citation_num}]: {page['filename']} page {page['page_number']}"}
            )
            content.append(
                {"type": "image_url", "image_url": {"url": data_uri}}
            )

    content.append(
        {
            "type": "text",
            "text": (
                f"Based on the numbered source pages shown above, answer "
                f"the following question. Ground your answer in the visible "
                f"content of these pages. Cite your sources using numbered "
                f"markers like [1], [2] when referencing information from "
                f"the source pages. Only cite sources you actually use. "
                f"If the pages do not contain enough information to answer, "
                f"say so.\n\n"
                f"Question: {query}"
            ),
        }
    )

    messages = []
    if history:
        # Bound to last 10 exchanges (20 messages)
        trimmed = history[-20:]
        for entry in trimmed:
            messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": content})

    try:
        response = client.chat.completions.create(
            model=QWEN3_VL_MODEL_NAME,
            messages=messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Generation unavailable: {e}]"
