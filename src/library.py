from qdrant_client import models

from src.config import QDRANT_COLLECTION_NAME, get_qdrant_client

_document_registry: dict[str, dict] = {}


def register_document(doc_id: str, filename: str, page_count: int) -> None:
    _document_registry[doc_id] = {
        "filename": filename,
        "page_count": page_count,
    }


def list_documents() -> list[dict]:
    return [
        {"doc_id": doc_id, **info}
        for doc_id, info in _document_registry.items()
    ]


def delete_document(doc_id: str) -> bool:
    if doc_id not in _document_registry:
        return False

    client = get_qdrant_client()
    client.delete(
        collection_name=QDRANT_COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchValue(value=doc_id),
                    )
                ]
            )
        ),
    )
    del _document_registry[doc_id]
    return True
