import contextlib
import io
from pathlib import Path
import sys
from typing import Literal, TypedDict

import fitz

from ._render import pdf_page_to_bytes
from ._table import rows_to_markdown
from ._text import normalize_block
from ._vision import describe_image


PDFRecord = TypedDict(
    "PDFRecord",
    {
        "text": str,
        "source_file": str,
        "doc_type": Literal["pdf"],
        "kind": Literal["text", "table"],
        "page_start": int,
        "page_end": int,
        "section": str,
        "has_table": bool,
        "has_visuals": bool,
        "vision_analyzed": bool,
    },
)


def _extract_table_rows(table: object) -> list[list[str]]:
    extract = getattr(table, "extract", None)
    if callable(extract):
        return extract()
    to_pandas = getattr(table, "to_pandas", None)
    if callable(to_pandas):
        df = to_pandas()
        rows = [list(df.columns.astype(str))]
        rows.extend(df.fillna("").astype(str).values.tolist())
        return rows
    return []


def parse_pdf(
    path: Path,
    enable_vision: bool = True,
    vision_provider: str | None = None,
) -> list[PDFRecord]:
    """
    Parse a PDF into normalized text/table records.
    """
    fitz.TOOLS.mupdf_display_warnings(False)
    fitz.set_messages(stream=sys.stderr)
    try:
        doc = fitz.open(path)
    except Exception as exc:
        raise ValueError(f"Cannot open PDF: {path}") from exc

    records: list[PDFRecord] = []
    page_count = len(doc)
    if page_count == 0:
        doc.close()
        return records

    text_parts: list[str] = []
    has_table_any = False
    has_visual_any = False
    vision_analyzed = False
    visual_sections: list[str] = []

    for idx, page in enumerate(doc, start=1):
        blocks = page.get_text("blocks") or []
        page_texts = []
        for block in blocks:
            if len(block) >= 5 and isinstance(block[4], str):
                normalized = normalize_block(block[4])
                if normalized:
                    page_texts.append(normalized)
        page_text = "\n".join(page_texts).strip()
        text_parts.append(f"\f[PAGE:{idx}]\f")
        if page_text:
            text_parts.append(page_text)

        with contextlib.redirect_stdout(io.StringIO()):
            finder = page.find_tables()
        tables = list(getattr(finder, "tables", finder) or [])
        for table in tables:
            rows = _extract_table_rows(table)
            markdown = rows_to_markdown(rows)
            if not markdown:
                continue
            has_table_any = True
            records.append(
                PDFRecord(
                    text=markdown,
                    source_file=path.name,
                    doc_type="pdf",
                    kind="table",
                    page_start=idx,
                    page_end=idx,
                    section="",
                    has_table=True,
                    has_visuals=False,
                    vision_analyzed=False,
                )
            )

        if enable_vision and page.get_images():
            has_visual_any = True
            vision_analyzed = True
            result = describe_image(
                pdf_page_to_bytes(page),
                provider=vision_provider,
            )
            if result:
                charts = result.get("charts", [])
                visual_sections.append(
                    "\n".join(
                        [
                            f"[Visual Content - Page {idx}]",
                            f"Summary: {result.get('summary', '')}",
                            f"Charts: {charts}",
                            f"Text: {result.get('text_content', '')}",
                        ]
                    )
                )

    full_text = "\n".join(text_parts).strip(" \n\t")
    if visual_sections:
        full_text = f"{full_text}\n\n" + "\n\n".join(visual_sections)

    if full_text:
        records.insert(
            0,
            PDFRecord(
                text=full_text,
                source_file=path.name,
                doc_type="pdf",
                kind="text",
                page_start=1,
                page_end=page_count,
                section="",
                has_table=has_table_any,
                has_visuals=has_visual_any,
                vision_analyzed=vision_analyzed,
            ),
        )

    doc.close()
    return records
