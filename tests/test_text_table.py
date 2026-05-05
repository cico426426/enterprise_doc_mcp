import unittest

from skills.parse_documents._table import rows_to_markdown
from skills.parse_documents._text import clean, iter_meaningful, merge_lines, normalize_block


class TextUtilsTests(unittest.TestCase):
    def test_clean_handles_special_chars_and_spacing(self) -> None:
        raw = "A\u00a0B\x0bC\u200b\n\n\nD"
        self.assertEqual(clean(raw), "A B\nC\n\nD")

    def test_merge_lines_hyphen_lower_digit_rules(self) -> None:
        lines = ["Long-", "term plan", "Revenue", "2025 guidance", "Done."]
        self.assertEqual(
            merge_lines(lines),
            ["Longterm plan", "Revenue 2025 guidance", "Done."],
        )

    def test_normalize_block_and_iter_meaningful(self) -> None:
        block = "Title\nok\nx\n \nBody"
        self.assertEqual(normalize_block(block), "Title ok x\n\nBody")
        self.assertEqual(iter_meaningful(block, min_len=2), ["Title", "ok", "Body"])


class TableUtilsTests(unittest.TestCase):
    def test_rows_to_markdown_empty(self) -> None:
        self.assertEqual(rows_to_markdown([]), "")

    def test_rows_to_markdown_header_only(self) -> None:
        expected = "| col1 | col2 |\n| --- | --- |"
        self.assertEqual(rows_to_markdown([["col1", "col2"]]), expected)

    def test_rows_to_markdown_escapes_pipe_and_newline(self) -> None:
        rows = [["h1"], ["a|b\nc"]]
        expected = "| h1 |\n| --- |\n| a\\|b c |"
        self.assertEqual(rows_to_markdown(rows), expected)


if __name__ == "__main__":
    unittest.main()
