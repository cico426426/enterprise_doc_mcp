import json
from typing import Any

from skills.chunk_and_index._store import list_sources
from skills.chunk_and_index.index import search_records


def _location(row: dict[str, Any]) -> str:
    if row.get("doc_type") == "pdf":
        page_start = int(row.get("page_start", 0) or 0)
        page_end = int(row.get("page_end", 0) or 0)
        if page_start and page_end:
            return f"Page {page_start}-{page_end}" if page_start != page_end else f"Page {page_start}"
    if row.get("doc_type") == "pptx":
        slide = int(row.get("slide_number", 0) or 0)
        if slide:
            return f"Slide {slide}"
    return ""


def _score(row: dict[str, Any]) -> float:
    if "rerank_score" in row:
        return float(row.get("rerank_score") or 0.0)
    return float(row.get("score") or 0.0)


def _format_result(rank: int, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": rank,
        "score": _score(row),
        "source": str(row.get("source_file", "")),
        "doc_type": str(row.get("doc_type", "")),
        "location": _location(row),
        "section": str(row.get("section", "")),
        "title": str(row.get("title", "")),
        "kind": str(row.get("kind", "")),
        "has_visuals": bool(row.get("has_visuals", False)),
        "text": str(row.get("text", "")),
    }


def run_search(
    query: str,
    top_k: int = 5,
    filename: str | None = None,
    rerank: bool = True,
) -> dict[str, Any]:
    clean_query = query.strip()
    bounded_top_k = max(1, min(int(top_k), 20))
    if not clean_query:
        return {
            "query": query,
            "reranked": rerank,
            "results": [],
            "total": 0,
        }

    rows = search_records(
        query=clean_query,
        top_k=bounded_top_k,
        filename=filename,
        rerank=rerank,
    )
    results = [_format_result(i + 1, row) for i, row in enumerate(rows)]
    return {
        "query": clean_query,
        "reranked": rerank,
        "results": results,
        "total": len(results),
    }


def run_list_documents() -> dict[str, Any]:
    sources = list_sources()
    return {
        "documents": sources,
        "total": len(sources),
    }


def sources_json() -> str:
    return json.dumps(run_list_documents(), ensure_ascii=False, indent=2)
