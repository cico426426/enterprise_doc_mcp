from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from skills.parse_documents._pdf import parse_pdf
from skills.parse_documents._pptx import parse_pptx
from skills.parse_documents.parse import parse_document


class ParseDispatchTests(TestCase):
    @patch("skills.parse_documents.parse.parse_pdf")
    def test_parse_document_dispatch_pdf(self, parse_pdf_mock: MagicMock) -> None:
        parse_pdf_mock.return_value = [{"kind": "text"}]
        path = Path("data/tsla-20231231-gen.pdf")
        out = parse_document(path, "pdf", enable_vision=False)
        self.assertEqual(out, [{"kind": "text"}])

    @patch("skills.parse_documents.parse.parse_pptx")
    def test_parse_document_dispatch_pptx(self, parse_pptx_mock: MagicMock) -> None:
        parse_pptx_mock.return_value = [{"kind": "slide"}]
        path = Path("data/GEP-June-2024-Presentation.pptx")
        out = parse_document(path, "pptx", enable_vision=False)
        self.assertEqual(out, [{"kind": "slide"}])

    def test_parse_document_invalid_type(self) -> None:
        with self.assertRaises(ValueError):
            parse_document("data/tsla-20231231-gen.pdf", "docx")  # type: ignore[arg-type]


class ParsePdfTests(TestCase):
    @patch("skills.parse_documents._pdf.fitz.open")
    def test_parse_pdf_adds_page_markers(self, fitz_open_mock: MagicMock) -> None:
        page = MagicMock()
        page.get_text.return_value = [(0, 0, 0, 0, "Hello page")]
        page.find_tables.return_value = []
        page.get_images.return_value = []
        doc = MagicMock()
        doc.__len__.return_value = 1
        doc.__iter__.return_value = iter([page])
        fitz_open_mock.return_value = doc

        out = parse_pdf(Path("x.pdf"), enable_vision=False)

        self.assertEqual(out[0]["kind"], "text")
        self.assertIn("\f[PAGE:1]\f", out[0]["text"])


class ParsePptxTests(TestCase):
    @patch("skills.parse_documents._pptx.Presentation")
    def test_parse_pptx_basic_slide_record(self, prs_mock: MagicMock) -> None:
        shape_title = MagicMock()
        shape_title.has_text_frame = True
        shape_title.text_frame.text = "Revenue"
        shape_title.has_table = False
        shape_title.shape_type = 1

        shape_body = MagicMock()
        shape_body.has_text_frame = True
        shape_body.text_frame.text = "Body text"
        shape_body.has_table = False
        shape_body.shape_type = 1

        shapes = MagicMock()
        shapes.title = MagicMock(text="Revenue")
        shapes.__iter__.return_value = iter([shape_title, shape_body])
        slide = MagicMock()
        slide.shapes = shapes
        slide.has_notes_slide = False

        prs = MagicMock()
        prs.slides = [slide]
        prs_mock.return_value = prs

        out = parse_pptx(Path("x.pptx"), enable_vision=False)
        self.assertEqual(out[0]["kind"], "slide")
        self.assertEqual(out[0]["title"], "Revenue")

