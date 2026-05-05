import os
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb

COLLECTION_NAME = "enterprise_docs"


def get_chroma_path() -> Path:
    path = Path(os.getenv("CHROMA_PATH", "chroma/"))
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache(maxsize=1)
def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(get_chroma_path()))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _meta_scalar(v: Any) -> str | int | float | bool:
    if isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def insert_chunks(chunks: list[dict]) -> None:
    if not chunks:
        return

    ids: list[str] = []
    docs: list[str] = []
    embs: list[list[float]] = []
    metas: list[dict] = []

    for chunk in chunks:
        if "id" not in chunk or "text" not in chunk:
            raise ValueError("Each chunk must include id and text")
        ids.append(str(chunk["id"]))
        docs.append(str(chunk["text"]))
        embs.append([float(x) for x in chunk.get("embedding", [])])
        meta = {
            k: _meta_scalar(v)
            for k, v in chunk.items()
            if k not in {"id", "text", "embedding"}
        }
        metas.append(meta)

    get_collection().upsert(
        ids=ids,
        documents=docs,
        embeddings=embs if all(embs) else None,
        metadatas=metas,
    )


def search(
    query_vec: list[float],
    top_k: int = 5,
    where: dict | None = None,
) -> list[dict]:
    if not query_vec:
        return []

    result = get_collection().query(
        query_embeddings=[query_vec],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    rows: list[dict] = []
    for i in range(len(ids)):
        row = {"id": ids[i], "text": docs[i], "score": float(distances[i])}
        if isinstance(metas[i], dict):
            row.update(metas[i])
        rows.append(row)
    rows.sort(key=lambda x: x["score"])
    return rows


def list_sources() -> list[dict]:
    result = get_collection().get(include=["metadatas"])
    metadatas = result.get("metadatas", []) or []
    bucket: dict[tuple[str, str], int] = defaultdict(int)

    for meta in metadatas:
        if not isinstance(meta, dict):
            continue
        source_file = str(meta.get("source_file", ""))
        doc_type = str(meta.get("doc_type", ""))
        if source_file:
            bucket[(source_file, doc_type)] += 1

    return [
        {
            "source_file": source_file,
            "doc_type": doc_type,
            "chunk_count": count,
        }
        for (source_file, doc_type), count in sorted(bucket.items())
    ]


def has_data() -> bool:
    return get_collection().count() > 0


def reset_collection() -> None:
    path = get_chroma_path()
    client = chromadb.PersistentClient(path=str(path))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    get_collection.cache_clear()
    get_collection()
