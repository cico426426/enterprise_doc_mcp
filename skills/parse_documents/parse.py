import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skills.parse_documents._pdf import parse_pdf
from skills.parse_documents._pptx import parse_pptx

LOGGER = logging.getLogger(__name__)


def parse_document(
    path: str | Path,
    doc_type: Literal["pdf", "pptx"],
    enable_vision: bool = True,
    vision_provider: str | None = None,
) -> list[dict]:
    file_path = Path(path)
    if not file_path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    if doc_type == "pdf":
        return list(parse_pdf(file_path, enable_vision=enable_vision, vision_provider=vision_provider))
    if doc_type == "pptx":
        return list(parse_pptx(file_path, enable_vision=enable_vision, vision_provider=vision_provider))
    raise ValueError(f"Unsupported doc_type: {doc_type}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse enterprise documents into normalized records.")
    parser.add_argument("--file", required=True, help="Input file path")
    parser.add_argument("--type", required=True, choices=["pdf", "pptx"], help="Document type")
    parser.add_argument("--no-vision", action="store_true", help="Disable vision analysis")
    parser.add_argument("--vision-provider", default=None, help="Vision provider override")
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args()
    records = parse_document(
        path=args.file,
        doc_type=args.type,
        enable_vision=not args.no_vision,
        vision_provider=args.vision_provider,
    )
    LOGGER.info("Parsed %d records from %s", len(records), args.file)
    print(json.dumps(records, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
