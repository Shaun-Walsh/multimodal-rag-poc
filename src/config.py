import os

import torch
from functools import lru_cache

COLQWEN2_MODEL_NAME = "vidore/colqwen2-v1.0"
QDRANT_COLLECTION_NAME = "colpali"
EMBEDDING_DIM = 128
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
QWEN3_VL_MODEL_NAME = "Qwen/Qwen3-VL-8B-Instruct"
DEFAULT_TOP_K = 5
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


@lru_cache(maxsize=1)
def get_model():
    from colpali_engine.models import ColQwen2, ColQwen2Processor

    model = ColQwen2.from_pretrained(
        COLQWEN2_MODEL_NAME,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    ).eval()
    processor = ColQwen2Processor.from_pretrained(COLQWEN2_MODEL_NAME)
    return model, processor


@lru_cache(maxsize=1)
def get_qdrant_client():
    from qdrant_client import QdrantClient, models

    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config={
            "colpali": models.VectorParams(
                size=EMBEDDING_DIM,
                distance=models.Distance.COSINE,
                multivector_config=models.MultiVectorConfig(
                    comparator=models.MultiVectorComparator.MAX_SIM
                ),
                hnsw_config=models.HnswConfigDiff(m=0),
            )
        },
    )
    return client
