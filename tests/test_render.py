from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from skills.parse_documents import _render


class RenderTests(TestCase):
    def test_pdf_page_to_bytes_success(self) -> None:
        page = MagicMock()
        pixmap = MagicMock()
        pixmap.tobytes.return_value = b"jpeg-bytes"
        page.get_pixmap.return_value = pixmap

        output = _render.pdf_page_to_bytes(page, scale=2.0)

        self.assertEqual(output, b"jpeg-bytes")
        page.get_pixmap.assert_called_once()
        pixmap.tobytes.assert_called_once_with("jpeg")

    def test_pdf_page_to_bytes_failure_raises_runtime_error(self) -> None:
        page = MagicMock()
        page.get_pixmap.side_effect = ValueError("bad page")

        with self.assertRaises(RuntimeError):
            _render.pdf_page_to_bytes(page)

    @patch("skills.parse_documents._render.Presentation")
    def test_pptx_slide_to_bytes_returns_first_picture(self, presentation_cls: MagicMock) -> None:
        picture_shape = MagicMock()
        picture_shape.shape_type = _render.MSO_SHAPE_TYPE.PICTURE
        picture_shape.image.blob = b"pic-bytes"

        text_shape = MagicMock()
        text_shape.shape_type = 1

        slide = MagicMock()
        slide.shapes = [text_shape, picture_shape]
        presentation = MagicMock()
        presentation.slides = [slide]
        presentation_cls.return_value = presentation

        result = _render.pptx_slide_to_bytes(0, Path("dummy.pptx"))
        self.assertEqual(result, b"pic-bytes")

    @patch("skills.parse_documents._render.Presentation")
    def test_pptx_slide_to_bytes_returns_none_without_picture(self, presentation_cls: MagicMock) -> None:
        text_shape = MagicMock()
        text_shape.shape_type = 1
        slide = MagicMock()
        slide.shapes = [text_shape]
        presentation = MagicMock()
        presentation.slides = [slide]
        presentation_cls.return_value = presentation

        result = _render.pptx_slide_to_bytes(0, Path("dummy.pptx"))
        self.assertIsNone(result)
