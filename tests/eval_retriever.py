import json
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Protocol

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skills.chunk_and_index.index import search_records


EVAL_QUERIES = [
    {
        "query": "Tesla 2023 total revenue",
        "expected_source": "tsla-20231231-gen.pdf",
        "reference": "Tesla's total revenues were $96.773 billion in 2023.",
    },
    {
        "query": "Tesla automotive segment gross margin",
        "expected_source": "tsla-20231231-gen.pdf",
        "reference": "Tesla's total automotive gross margin was 19.4% in 2023.",
    },
    {
        "query": "World Bank GDP growth forecast",
        "expected_source": "GEP-June-2024-Presentation.pptx",
        "reference": "The World Bank presentation discusses global GDP growth forecasts.",
    },
    {
        "query": "risk factors litigation Tesla",
        "expected_source": "tsla-20231231-gen.pdf",
        "reference": "Tesla reports risk factors related to litigation, claims, and regulatory proceedings.",
    },
    {
        "query": "quarterly revenue table",
        "expected_source": "tsla-20231231-gen.pdf",
        "reference": "Tesla's filing includes tabular revenue information for reported periods.",
    },
    {
        "query": "revenue chart visual analysis",
        "expected_source": "tsla-20231231-gen.pdf",
        "reference": "Visual analysis should retrieve chart or visual context related to revenue.",
    },
]


class ContextJudge(Protocol):
    def score(self, user_input: str, reference: str, retrieved_contexts: list[str]) -> dict:
        """Return context_precision and context_recall scores in the 0..1 range."""


@dataclass
class EvalResult:
    query: str
    context_precision: float
    context_recall: float
    top1_source: str
    top1_location: str
    top1_score: float

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
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


class RagasContextJudge:
    def __init__(self, model: str | None = None) -> None:
        try:
            from dotenv import load_dotenv
            from openai import AsyncOpenAI
            from ragas.llms import llm_factory
            from ragas.metrics.collections import ContextPrecision, ContextRecall
        except ImportError as exc:
            raise RuntimeError(
                "Ragas retriever evaluation requires python-dotenv, ragas, and openai. "
                "Install project dependencies, then set OPENAI_API_KEY."
            ) from exc

        load_dotenv(PROJECT_ROOT / ".env")
        judge_model = model or os.getenv("RAGAS_JUDGE_MODEL", "gpt-4o-mini")
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        llm = llm_factory(judge_model, client=client)
        self._context_precision = ContextPrecision(llm=llm)
        self._context_recall = ContextRecall(llm=llm)

    def score(self, user_input: str, reference: str, retrieved_contexts: list[str]) -> dict:
        precision = self._context_precision.score(
            user_input=user_input,
            reference=reference,
            retrieved_contexts=retrieved_contexts,
        )
        recall = self._context_recall.score(
            user_input=user_input,
            reference=reference,
            retrieved_contexts=retrieved_contexts,
        )
        return {
            "context_precision": float(precision.value),
            "context_recall": float(recall.value),
        }


def _contexts(rows: list[dict]) -> list[str]:
    return [str(row.get("text", "")) for row in rows if str(row.get("text", "")).strip()]


def run_eval(top_k: int = 5, judge: ContextJudge | None = None) -> dict:
    context_judge = judge or RagasContextJudge()
    results: list[EvalResult] = []
    evaluated_count = 0

    for case in EVAL_QUERIES:
        query = case["query"]
        expected_source = case["expected_source"]
        reference = case["reference"]
        try:
            rows = search_records(query=query, top_k=top_k, rerank=True)
        except Exception:
            rows = []
        contexts = _contexts(rows)
        scores = (
            context_judge.score(
                user_input=query,
                reference=reference,
                retrieved_contexts=contexts,
            )
            if contexts
            else {"context_precision": 0.0, "context_recall": 0.0}
        )
        if rows:
            top1 = rows[0]
            top1_source = str(top1.get("source_file", ""))
            evaluated_count += 1
            result = EvalResult(
                query=query,
                context_precision=float(scores["context_precision"]),
                context_recall=float(scores["context_recall"]),
                top1_source=top1_source,
                top1_location=_location(top1),
                top1_score=float(top1.get("rerank_score", top1.get("score", 0.0))),
            )
        else:
            evaluated_count += 1
            result = EvalResult(
                query=query,
                context_precision=0.0,
                context_recall=0.0,
                top1_source="",
                top1_location="",
                top1_score=0.0,
            )
        results.append(result)

    rows_dict = [r.to_dict() for r in results]
    avg_precision = sum(row["context_precision"] for row in rows_dict) / max(1, evaluated_count)
    avg_recall = sum(row["context_recall"] for row in rows_dict) / max(1, evaluated_count)
    return {
        "context_precision": avg_precision,
        "context_recall": avg_recall,
        "ragas_context_score": (avg_precision + avg_recall) / 2,
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
