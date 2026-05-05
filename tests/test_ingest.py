from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

import scripts.ingest as ingest


class IngestTests(TestCase):
    @patch("scripts.ingest.has_data", return_value=True)
    @patch("scripts.ingest.reset_collection")
    def test_skip_if_exists(self, reset_mock: MagicMock, has_data_mock: MagicMock) -> None:
        out = ingest.run_ingest(
            data_dir=Path("data"),
            reset=False,
            skip_if_exists=True,
            enable_vision=False,
        )
        self.assertTrue(out["skipped"])
        reset_mock.assert_not_called()
        has_data_mock.assert_called_once()

    @patch("scripts.ingest.index_records")
    @patch("scripts.ingest.parse_document")
    @patch("scripts.ingest._discover_files")
    @patch("scripts.ingest.has_data", return_value=False)
    def test_ingest_processes_and_continues_on_error(
        self,
        has_data_mock: MagicMock,
        discover_mock: MagicMock,
        parse_mock: MagicMock,
        index_mock: MagicMock,
    ) -> None:
        discover_mock.return_value = [Path("a.pdf"), Path("b.pptx")]
        parse_mock.side_effect = [[{"text": "x"}], RuntimeError("boom")]
        index_mock.return_value = {"chunk_count": 3}

        out = ingest.run_ingest(
            data_dir=Path("data"),
            reset=False,
            skip_if_exists=False,
            enable_vision=False,
        )
        self.assertEqual(out["processed_files"], 1)
        self.assertEqual(out["failed_files"], 1)
        self.assertEqual(out["chunk_count"], 3)
        has_data_mock.assert_not_called()

    @patch("scripts.ingest._discover_files", return_value=[])
    def test_ingest_empty_directory(self, discover_mock: MagicMock) -> None:
        out = ingest.run_ingest(
            data_dir=Path("empty"),
            reset=False,
            skip_if_exists=False,
            enable_vision=False,
        )
        self.assertEqual(out["processed_files"], 0)
        self.assertFalse(out["skipped"])

    @patch("scripts.ingest.reset_collection")
    @patch("scripts.ingest._discover_files", return_value=[])
    def test_reset_flag_calls_reset(self, discover_mock: MagicMock, reset_mock: MagicMock) -> None:
        ingest.run_ingest(
            data_dir=Path("empty"),
            reset=True,
            skip_if_exists=False,
            enable_vision=False,
        )
        reset_mock.assert_called_once()
