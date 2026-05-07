import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Literal

def _find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "skills").is_dir() and (candidate / "plan").is_dir():
            return candidate
    raise RuntimeError(f"Could not find project root from {start}")


PROJECT_ROOT = _find_project_root(Path(__file__).resolve().parent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skills.parse_documents._pdf import parse_pdf
from skills.parse_documents._pptx import parse_pptx

LOGGER = logging.getLogger(__name__)


def _doc_type_for_path(path: Path) -> Literal["pdf", "pptx"]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".pptx":
        return "pptx"
    raise ValueError(f"Unsupported file type: {path}")


def discover_documents(source_dir: str | Path) -> list[Path]:
    directory = Path(source_dir)
    if not directory.exists():
        raise ValueError(f"Source directory does not exist: {directory}")
    if not directory.is_dir():
        raise ValueError(f"Source path is not a directory: {directory}")
    files = [*directory.glob("*.pdf"), *directory.glob("*.pptx")]
    return sorted(files, key=lambda p: p.name.lower())


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


def parse_documents(
    source_dir: str | Path,
    enable_vision: bool = True,
    vision_provider: str | None = None,
) -> list[dict]:
    records: list[dict] = []
    for file_path in discover_documents(source_dir):
        records.extend(
            parse_document(
                path=file_path,
                doc_type=_doc_type_for_path(file_path),
                enable_vision=enable_vision,
                vision_provider=vision_provider,
            )
        )
    return records


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse enterprise documents into normalized records.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Input file path")
    source.add_argument(
        "--source-dir",
        "--data-dir",
        "--input-dir",
        dest="source_dir",
        help="Directory containing .pdf/.pptx files",
    )
    parser.add_argument("--type", choices=["pdf", "pptx"], help="Document type; required with --file")
    parser.add_argument("--no-vision", action="store_true", help="Disable vision analysis")
    parser.add_argument("--vision-provider", default=None, help="Vision provider override")
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args()
    if args.file:
        if not args.type:
            parser.error("--type is required with --file")
        records = parse_document(
            path=args.file,
            doc_type=args.type,
            enable_vision=not args.no_vision,
            vision_provider=args.vision_provider,
        )
        LOGGER.info("Parsed %d records from %s", len(records), args.file)
    else:
        records = parse_documents(
            source_dir=args.source_dir,
            enable_vision=not args.no_vision,
            vision_provider=args.vision_provider,
        )
        LOGGER.info("Parsed %d records from %s", len(records), args.source_dir)
    print(json.dumps(records, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
