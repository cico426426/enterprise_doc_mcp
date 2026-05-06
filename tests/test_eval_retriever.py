from unittest import TestCase
from unittest.mock import patch

from tests.eval_retriever import hit_rate, run_eval


class EvalRetrieverTests(TestCase):
    def test_hit_rate_true_when_all_keywords_in_any_row(self) -> None:
        rows = [{"text": "Total revenues were 96,773 in 2023."}, {"text": "other"}]
        self.assertTrue(hit_rate(rows, ["96,773", "total revenues"]))

    def test_hit_rate_false_when_missing_keyword(self) -> None:
        rows = [{"text": "Revenue reached 97.7 in 2023."}]
        self.assertFalse(hit_rate(rows, ["97.7", "revenue", "billion"]))

    @patch("tests.eval_retriever.search_records")
    def test_run_eval_shape(self, search_mock) -> None:
        search_mock.return_value = [
            {
                "text": "Visual Content revenue chart details",
                "source_file": "tsla-20231231-gen.pdf",
                "doc_type": "pdf",
                "page_start": 5,
                "page_end": 6,
                "rerank_score": 1.2,
            }
        ]
        out = run_eval(top_k=3)
        self.assertIn("hit_rate", out)
        self.assertIn("results", out)
        self.assertEqual(len(out["results"]), 6)
