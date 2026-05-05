from unittest import TestCase
from unittest.mock import MagicMock, patch

from skills.chunk_and_index import _store
from skills.chunk_and_index.index import _extract_page_range, _make_chunk_id, index_records, search_records


class IndexHelpersTests(TestCase):
    def test_make_chunk_id(self) -> None:
        self.assertEqual(_make_chunk_id("tsla-20231231-gen.pdf", 3), "tsla-20231231-gen_0003")

    def test_extract_page_range(self) -> None:
        text = "\f[PAGE:5]\f alpha \f[PAGE:6]\f beta"
        self.assertEqual(_extract_page_range(text, 0, len(text)), (5, 6))
        self.assertEqual(_extract_page_range("plain text", 0, 10), (0, 0))


class IndexFlowTests(TestCase):
    @patch("skills.chunk_and_index.index.insert_chunks")
    @patch("skills.chunk_and_index.index.embed")
    @patch("skills.chunk_and_index.index.SentenceSplitter")
    def test_index_records_pdf_and_pptx(self, splitter_cls: MagicMock, embed_mock: MagicMock, insert_mock: MagicMock) -> None:
        node = MagicMock()
        node.get_content.return_value = "\f[PAGE:2]\f Revenue grew."
        splitter = MagicMock()
        splitter.get_nodes_from_documents.return_value = [node]
        splitter_cls.return_value = splitter
        embed_mock.return_value = [[0.1, 0.2], [0.3, 0.4]]

        records = [
            {
                "text": "\f[PAGE:1]\f Hello \f[PAGE:2]\f World",
                "source_file": "a.pdf",
                "doc_type": "pdf",
                "kind": "text",
                "section": "",
                "has_table": False,
                "has_visuals": False,
                "vision_analyzed": False,
            },
            {
                "text": "Slide body",
                "source_file": "b.pptx",
                "doc_type": "pptx",
                "kind": "slide",
                "slide_number": 1,
                "title": "T",
                "has_table": False,
                "has_visuals": False,
                "vision_analyzed": False,
            },
        ]
        out = index_records(records)
        self.assertEqual(out["chunk_count"], 2)
        insert_mock.assert_called_once()

    @patch("skills.chunk_and_index.index.rerank_results")
    @patch("skills.chunk_and_index.index.search")
    @patch("skills.chunk_and_index.index.embed")
    def test_search_records(self, embed_mock: MagicMock, search_mock: MagicMock, rerank_mock: MagicMock) -> None:
        embed_mock.return_value = [[0.9, 0.8]]
        search_mock.return_value = [{"id": "x", "text": "abc", "score": 0.1}]
        rerank_mock.return_value = [{"id": "x", "text": "abc", "score": 0.1, "rerank_score": 1.0}]
        out = search_records("query", top_k=1, filename="a.pdf", rerank=True)
        self.assertEqual(len(out), 1)
        search_mock.assert_called_once()
        rerank_mock.assert_called_once()


class StoreTests(TestCase):
    def test_insert_and_search_shape(self) -> None:
        collection = MagicMock()
        with patch("skills.chunk_and_index._store.get_collection", return_value=collection):
            _store.insert_chunks(
                [
                    {
                        "id": "c1",
                        "text": "hello",
                        "embedding": [0.1, 0.2],
                        "source_file": "a.pdf",
                        "doc_type": "pdf",
                    }
                ]
            )
            collection.upsert.assert_called_once()

            collection.query.return_value = {
                "ids": [["c1"]],
                "documents": [["hello"]],
                "metadatas": [[{"source_file": "a.pdf", "doc_type": "pdf"}]],
                "distances": [[0.12]],
            }
            rows = _store.search([0.1, 0.2], top_k=1)
            self.assertEqual(rows[0]["id"], "c1")
            self.assertEqual(rows[0]["score"], 0.12)

    def test_list_sources(self) -> None:
        collection = MagicMock()
        collection.get.return_value = {
            "metadatas": [
                {"source_file": "a.pdf", "doc_type": "pdf"},
                {"source_file": "a.pdf", "doc_type": "pdf"},
                {"source_file": "b.pptx", "doc_type": "pptx"},
            ]
        }
        with patch("skills.chunk_and_index._store.get_collection", return_value=collection):
            out = _store.list_sources()
            self.assertEqual(len(out), 2)
            self.assertEqual(out[0]["chunk_count"], 2)
