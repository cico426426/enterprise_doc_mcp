from unittest import TestCase
from unittest.mock import patch

from mcp_server._search import run_list_documents, run_search, sources_json


class SearchFormattingTests(TestCase):
    @patch("mcp_server._search.search_records")
    def test_run_search_formats_pdf_result(self, search_mock) -> None:
        search_mock.return_value = [
            {
                "text": "Revenue text",
                "source_file": "tsla.pdf",
                "doc_type": "pdf",
                "page_start": 5,
                "page_end": 6,
                "section": "Revenue",
                "kind": "text",
                "has_visuals": True,
                "rerank_score": 1.25,
            }
        ]

        out = run_search(" revenue ", top_k=50, filename="tsla.pdf")

        search_mock.assert_called_once_with(
            query="revenue",
            top_k=20,
            filename="tsla.pdf",
            rerank=True,
        )
        self.assertEqual(out["query"], "revenue")
        self.assertEqual(out["total"], 1)
        self.assertEqual(out["results"][0]["rank"], 1)
        self.assertEqual(out["results"][0]["location"], "Page 5-6")
        self.assertEqual(out["results"][0]["source"], "tsla.pdf")
        self.assertTrue(out["results"][0]["has_visuals"])

    @patch("mcp_server._search.search_records")
    def test_run_search_formats_pptx_result_without_rerank(self, search_mock) -> None:
        search_mock.return_value = [
            {
                "text": "Forecast slide",
                "source_file": "gep.pptx",
                "doc_type": "pptx",
                "slide_number": 4,
                "title": "Forecast",
                "kind": "slide",
                "score": 0.12,
            }
        ]

        out = run_search("forecast", top_k=3, rerank=False)

        self.assertFalse(out["reranked"])
        self.assertEqual(out["results"][0]["location"], "Slide 4")
        self.assertEqual(out["results"][0]["title"], "Forecast")
        self.assertEqual(out["results"][0]["score"], 0.12)

    @patch("mcp_server._search.search_records")
    def test_empty_query_does_not_search(self, search_mock) -> None:
        out = run_search("  ")

        search_mock.assert_not_called()
        self.assertEqual(out["total"], 0)
        self.assertEqual(out["results"], [])

    @patch("mcp_server._search.list_sources")
    def test_list_documents_and_resource_json(self, list_sources_mock) -> None:
        list_sources_mock.return_value = [
            {"source_file": "a.pdf", "doc_type": "pdf", "chunk_count": 2}
        ]

        out = run_list_documents()

        self.assertEqual(out["total"], 1)
        self.assertEqual(out["documents"][0]["source_file"], "a.pdf")
        self.assertIn('"source_file": "a.pdf"', sources_json())
