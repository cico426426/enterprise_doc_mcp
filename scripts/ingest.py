import argparse
import logging
import sys
from pathlib import Path

def _find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "skills").is_dir() and (candidate / "plan").is_dir():
            return candidate
    raise RuntimeError(f"Could not find project root from {start}")


PROJECT_ROOT = _find_project_root(Path(__file__).resolve().parent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from skills.chunk_and_index._store import has_data, reset_collection
from skills.chunk_and_index.index import index_records
from skills.parse_documents.parse import parse_document

LOGGER = logging.getLogger(__name__)


def _discover_files(data_dir: Path) -> list[Path]:
    if not data_dir.exists():
        return []
    files = [*data_dir.glob("*.pdf"), *data_dir.glob("*.pptx")]
    return sorted(files, key=lambda p: p.name.lower())


def _doc_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".pptx":
        return "pptx"
    raise ValueError(f"Unsupported file type: {path}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest enterprise docs into ChromaDB.")
    parser.add_argument("--reset", action="store_true", help="Reset collection before ingest")
    parser.add_argument("--no-vision", action="store_true", help="Disable vision analysis")
    parser.add_argument("--vision-provider", default=None, help="Vision provider override")
    parser.add_argument("--skip-if-exists", action="store_true", help="Skip ingest if collection already has data")
    parser.add_argument("--data-dir", default="data", help="Directory containing .pdf/.pptx files")
    parser.add_argument(
        "--source-dir",
        dest="data_dir",
        help="Alias for --data-dir; accepted for consistency with parse-enterprise-documents",
    )
    parser.add_argument(
        "--input-dir",
        dest="data_dir",
        help="Alias for --data-dir; accepted for common directory-input wording",
    )
    return parser


def run_ingest(
    data_dir: Path,
    reset: bool = False,
    skip_if_exists: bool = False,
    enable_vision: bool = True,
    vision_provider: str | None = None,
) -> dict:
    if reset:
        LOGGER.info("Resetting collection")
        reset_collection()

    if skip_if_exists and has_data():
        LOGGER.info("Collection already has data, skipping ingest")
        return {"processed_files": 0, "failed_files": 0, "chunk_count": 0, "skipped": True}

    files = _discover_files(data_dir)
    if not files:
        LOGGER.warning("No PDF/PPTX files found in %s", data_dir)
        return {"processed_files": 0, "failed_files": 0, "chunk_count": 0, "skipped": False}

    processed = 0
    failed = 0
    total_chunks = 0

    for file_path in files:
        try:
            doc_type = _doc_type(file_path)
            records = parse_document(
                path=file_path,
                doc_type=doc_type,  # type: ignore[arg-type]
                enable_vision=enable_vision,
                vision_provider=vision_provider,
            )
            indexed = index_records(records)
            processed += 1
            total_chunks += int(indexed.get("chunk_count", 0))
            LOGGER.info(
                "Ingested %s (%s): records=%d chunks=%d",
                file_path,
                doc_type,
                len(records),
                indexed.get("chunk_count", 0),
            )
        except Exception as exc:
            failed += 1
            LOGGER.error("Failed ingest for %s: %s", file_path, exc)

    return {
        "processed_files": processed,
        "failed_files": failed,
        "chunk_count": total_chunks,
        "skipped": False,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _build_parser().parse_args()
    summary = run_ingest(
        data_dir=Path(args.data_dir),
        reset=args.reset,
        skip_if_exists=args.skip_if_exists,
        enable_vision=not args.no_vision,
        vision_provider=args.vision_provider,
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
