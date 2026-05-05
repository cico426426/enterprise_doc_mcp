from functools import lru_cache

from sentence_transformers import CrossEncoder


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(
    query: str,
    results: list[dict],
    top_k: int,
) -> list[dict]:
    if not results:
        return []

    pairs = [(query, r.get("text", "")) for r in results]
    scores = get_reranker().predict(pairs)

    enriched = []
    for item, score in zip(results, scores):
        row = dict(item)
        row["rerank_score"] = float(score)
        enriched.append(row)

    enriched.sort(key=lambda x: x["rerank_score"], reverse=True)
    return enriched[:top_k]
