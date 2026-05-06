from unittest import TestCase
from unittest.mock import MagicMock, patch

from tests.eval_retriever import PROJECT_ROOT, RagasContextJudge, run_eval


class FakeJudge:
    def score(self, user_input: str, reference: str, retrieved_contexts: list[str]) -> dict:
        return {
            "context_precision": 0.75 if retrieved_contexts else 0.0,
            "context_recall": 0.5 if reference else 0.0,
        }


class EvalRetrieverTests(TestCase):
    @patch("tests.eval_retriever.search_records")
    def test_run_eval_uses_context_scores(self, search_mock) -> None:
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
        out = run_eval(top_k=3, judge=FakeJudge())
        self.assertEqual(out["context_precision"], 0.75)
        self.assertEqual(out["context_recall"], 0.5)
        self.assertEqual(out["ragas_context_score"], 0.625)
        self.assertIn("results", out)
        self.assertEqual(len(out["results"]), 6)
        self.assertIn("context_precision", out["results"][0])
        self.assertIn("context_recall", out["results"][0])

    @patch("tests.eval_retriever.search_records")
    def test_run_eval_scores_empty_results_as_zero(self, search_mock) -> None:
        search_mock.return_value = []
        out = run_eval(top_k=3, judge=FakeJudge())
        self.assertEqual(out["context_precision"], 0.0)
        self.assertEqual(out["context_recall"], 0.0)
        self.assertEqual(out["ragas_context_score"], 0.0)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=False)
    @patch("ragas.metrics.collections.ContextRecall")
    @patch("ragas.metrics.collections.ContextPrecision")
    @patch("ragas.llms.llm_factory")
    @patch("openai.AsyncOpenAI")
    @patch("dotenv.load_dotenv")
    def test_ragas_judge_loads_dotenv(
        self,
        load_dotenv_mock,
        openai_mock,
        llm_factory_mock,
        context_precision_mock,
        context_recall_mock,
    ) -> None:
        openai_mock.return_value = MagicMock()
        llm_factory_mock.return_value = MagicMock()
        RagasContextJudge()
        load_dotenv_mock.assert_called_once_with(PROJECT_ROOT / ".env")
