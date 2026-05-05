import os
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    model_name = os.getenv("EMBED_MODEL_NAME", "BAAI/bge-small-en-v1.5")
    cache_dir = os.getenv("EMBED_CACHE_DIR")
    if cache_dir:
        return SentenceTransformer(model_name, cache_folder=cache_dir)
    return SentenceTransformer(model_name)


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = get_model().encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )
    return np.asarray(vectors, dtype=np.float32).tolist()
