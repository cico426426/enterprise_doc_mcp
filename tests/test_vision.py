import unittest
from unittest.mock import MagicMock, patch

from skills.parse_documents._vision import describe_image


class VisionTests(unittest.TestCase):
    def test_empty_bytes_returns_none(self) -> None:
        self.assertIsNone(describe_image(b""))

    def test_provider_resolution_param_over_env(self) -> None:
        with patch("skills.parse_documents._vision.os.getenv") as getenv_mock:
            getenv_mock.side_effect = lambda k, d="": {
                "VISION_PROVIDER": "gemini",
                "OPENAI_API_KEY": "12345678",
                "OPENAI_VISION_MODEL": "gpt-4o-mini",
            }.get(k, d)
            with patch("skills.parse_documents._vision._describe_with_openai") as fn:
                fn.return_value = {
                    "summary": "s",
                    "charts": [],
                    "text_content": "t",
                    "has_data": False,
                }
                out = describe_image(b"\xff\xd8\xffabc", provider="openai")
                self.assertIsNotNone(out)
                fn.assert_called_once()

    def test_missing_key_returns_none(self) -> None:
        with patch("skills.parse_documents._vision.os.getenv", return_value=""):
            self.assertIsNone(describe_image(b"\xff\xd8\xffabc", provider="gemini"))

    def test_network_error_returns_none(self) -> None:
        mapping = {"GEMINI_API_KEY": "abcd1234efgh5678"}
        with patch("skills.parse_documents._vision.os.getenv", side_effect=lambda k, d="": mapping.get(k, d)):
            with patch("skills.parse_documents._vision._describe_with_gemini", side_effect=RuntimeError("boom")):
                self.assertIsNone(describe_image(b"\xff\xd8\xffabc", provider="gemini"))

    def test_schema_mismatch_returns_none(self) -> None:
        mapping = {"OPENAI_API_KEY": "abcd1234efgh5678"}
        with patch("skills.parse_documents._vision.os.getenv", side_effect=lambda k, d="": mapping.get(k, d)):
            with patch("skills.parse_documents._vision._describe_with_openai", return_value={"bad": "shape"}):
                self.assertIsNone(describe_image(b"\xff\xd8\xffabc", provider="openai"))

    @patch("skills.parse_documents._vision.OpenAI", create=True)
    def test_openai_output_text_json_path(self, openai_cls: MagicMock) -> None:
        # Keep this test focused on describe_image behavior and parsing.
        with patch("skills.parse_documents._vision._describe_with_openai") as fn:
            fn.return_value = {
                "summary": "one",
                "charts": [{"type": "bar", "title": "rev", "key_findings": "up"}],
                "text_content": "txt",
                "has_data": True,
            }
            with patch("skills.parse_documents._vision.os.getenv", side_effect=lambda k, d="": {"OPENAI_API_KEY": "abcd1234efgh5678"}.get(k, d)):
                out = describe_image(b"\xff\xd8\xffabc", provider="openai")
                self.assertEqual(out["summary"], "one")


if __name__ == "__main__":
    unittest.main()
