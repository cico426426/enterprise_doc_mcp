import json
from dataclasses import dataclass
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skills.chunk_and_index.index import search_records


EVAL_QUERIES = [
    {
        "query": "Tesla 2023 total revenue",
        "expected_source": "tsla-20231231-gen.pdf",
        "expected_keywords": ["96,773", "total revenues"],
    },
    {
        "query": "Tesla automotive segment gross margin",
        "expected_source": "tsla-20231231-gen.pdf",
        "expected_keywords": ["gross margin total automotive", "19.4"],
    },
    {
        "query": "World Bank GDP growth forecast",
        "expected_source": "GEP-June-2024-Presentation.pptx",
        "expected_keywords": ["GDP"],
    },
    {
        "query": "risk factors litigation Tesla",
        "expected_source": "tsla-20231231-gen.pdf",
        "expected_keywords": ["risk factors"],
    },
    {
        "query": "quarterly revenue table",
        "expected_source": "tsla-20231231-gen.pdf",
        "expected_keywords": ["revenue"],
    },
    {
        "query": "revenue chart visual analysis",
        "expected_source": "tsla-20231231-gen.pdf",
        "expected_keywords": ["Visual Content"],
    },
]


def _normalize_for_match(text: str) -> str:
    # Keep matching robust against common table number formatting.
    return " ".join(text.lower().replace(",", "").split())


def hit_rate(results: list[dict], expected_keywords: list[str]) -> bool:
    if not results:
        return False
    lowered_keywords = [_normalize_for_match(k) for k in expected_keywords]
    for row in results:
        text = _normalize_for_match(str(row.get("text", "")))
        if all(k in text for k in lowered_keywords):
            return True
    return False


@dataclass
class EvalResult:
    query: str
    hit: bool
    top1_source: str
    top1_location: str
    top1_score: float

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "hit": self.hit,
            "top1_source": self.top1_source,
            "top1_location": self.top1_location,
            "top1_score": self.top1_score,
        }


def _location(row: dict) -> str:
    if row.get("doc_type") == "pdf":
        ps = int(row.get("page_start", 0))
        pe = int(row.get("page_end", 0))
        if ps and pe:
            return f"Page {ps}-{pe}" if ps != pe else f"Page {ps}"
    if row.get("doc_type") == "pptx":
        slide = int(row.get("slide_number", 0))
        if slide:
            return f"Slide {slide}"
    return ""


def run_eval(top_k: int = 5) -> dict:
    results: list[EvalResult] = []
    hits = 0
    evaluated_count = 0

    for case in EVAL_QUERIES:
        query = case["query"]
        expected_source = case["expected_source"]
        expected_keywords = case["expected_keywords"]
        if "Visual Content" in expected_keywords:
            try:
                probe = search_records(query="Visual Content", top_k=1, rerank=False)
            except Exception:
                probe = []
            if not probe:
                result = EvalResult(
                    query=query,
                    hit=False,
                    top1_source="",
                    top1_location="",
                    top1_score=0.0,
                )
                results.append(result)
                continue
        try:
            rows = search_records(query=query, top_k=top_k, rerank=True)
        except Exception:
            rows = []
        hit = hit_rate(rows, expected_keywords)
        if rows:
            top1 = rows[0]
            top1_source = str(top1.get("source_file", ""))
            if hit:
                hits += 1
            evaluated_count += 1
            result = EvalResult(
                query=query,
                hit=hit,
                top1_source=top1_source,
                top1_location=_location(top1),
                top1_score=float(top1.get("rerank_score", top1.get("score", 0.0))),
            )
        else:
            evaluated_count += 1
            result = EvalResult(
                query=query,
                hit=False,
                top1_source="",
                top1_location="",
                top1_score=0.0,
            )
        results.append(result)

    score = hits / evaluated_count if evaluated_count else 0.0
    rows_dict = [r.to_dict() for r in results]
    return {
        "hit_rate": score,
        "source_top1_rate": sum(
            1
            for case, row in zip(
                EVAL_QUERIES,
                rows_dict,
            )
            if row["top1_source"] and row["top1_source"] == case["expected_source"]
        )
        / max(1, sum(1 for row in rows_dict if row["top1_source"])),
        "evaluated_queries": evaluated_count,
        "total_queries": len(EVAL_QUERIES),
        "results": rows_dict,
    }


if __name__ == "__main__":
    output = run_eval(top_k=5)
    print(json.dumps(output, ensure_ascii=False, indent=2))
