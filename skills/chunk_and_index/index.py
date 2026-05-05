import re
from collections import defaultdict

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

from skills.chunk_and_index._embed import embed
from skills.chunk_and_index._rerank import rerank as rerank_results
from skills.chunk_and_index._store import insert_chunks, search

PAGE_PATTERN = re.compile(r"\f\[PAGE:(\d+)\]\f")


def _extract_page_range(text: str, start: int, end: int) -> tuple[int, int]:
    _ = (start, end)
    matches = [int(m) for m in PAGE_PATTERN.findall(text)]
    if not matches:
        return (0, 0)
    return (min(matches), max(matches))


def _make_chunk_id(source_file: str, chunk_index: int) -> str:
    stem = source_file.rsplit(".", 1)[0]
    return f"{stem}_{chunk_index:04d}"


def _clean_page_markers(text: str) -> str:
    return PAGE_PATTERN.sub("", text).strip()


def index_records(
    records: list[dict],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> dict:
    chunks: list[dict] = []
    source_files: set[str] = set()
    file_counters: dict[str, int] = defaultdict(int)

    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    for record in records:
        source_file = str(record.get("source_file", ""))
        if not source_file:
            continue
        source_files.add(source_file)

        kind = record.get("kind")
        doc_type = record.get("doc_type")
        text = str(record.get("text", "")).strip()
        if not text:
            continue

        if doc_type == "pdf" and kind == "text":
            nodes = splitter.get_nodes_from_documents([Document(text=text)])
            for node in nodes:
                node_text = node.get_content()
                page_start, page_end = _extract_page_range(node_text, 0, 0)
                chunk_text = _clean_page_markers(node_text)
                if not chunk_text:
                    continue
                idx = file_counters[source_file]
                file_counters[source_file] += 1
                chunks.append(
                    {
                        "id": _make_chunk_id(source_file, idx),
                        "text": chunk_text,
                        "source_file": source_file,
                        "doc_type": "pdf",
                        "page_start": page_start,
                        "page_end": page_end,
                        "chunk_index": idx,
                        "kind": record.get("kind", "text"),
                        "section": record.get("section", ""),
                        "has_table": bool(record.get("has_table", False)),
                        "has_visuals": bool(record.get("has_visuals", False)),
                        "vision_analyzed": bool(record.get("vision_analyzed", False)),
                    }
                )
            continue

        idx = file_counters[source_file]
        file_counters[source_file] += 1
        chunk = {
            "id": _make_chunk_id(source_file, idx),
            "text": text,
            "source_file": source_file,
            "doc_type": str(doc_type),
            "chunk_index": idx,
            "kind": str(kind),
            "has_table": bool(record.get("has_table", False)),
            "has_visuals": bool(record.get("has_visuals", False)),
            "vision_analyzed": bool(record.get("vision_analyzed", False)),
        }
        if doc_type == "pptx":
            chunk["slide_number"] = int(record.get("slide_number", 0))
            chunk["title"] = str(record.get("title", ""))
        elif doc_type == "pdf":
            chunk["page_start"] = int(record.get("page_start", 0))
            chunk["page_end"] = int(record.get("page_end", 0))
            chunk["section"] = str(record.get("section", ""))
        chunks.append(chunk)

    vectors = embed([c["text"] for c in chunks])
    for i, vec in enumerate(vectors):
        chunks[i]["embedding"] = vec
    insert_chunks(chunks)

    return {
        "chunk_count": len(chunks),
        "source_files": sorted(source_files),
    }


def search_records(
    query: str,
    top_k: int = 5,
    filename: str | None = None,
    rerank: bool = True,
) -> list[dict]:
    if not query.strip():
        return []

    query_vec = embed([query])[0]
    where = {"source_file": filename} if filename else None
    initial = search(query_vec, top_k=20, where=where)

    if rerank:
        return rerank_results(query=query, results=initial, top_k=top_k)
    return initial[:top_k]
