import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server import mcp
from scripts.ingest import run_ingest
from skills.chunk_and_index._store import has_data

LOGGER = logging.getLogger(__name__)


def _enabled(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _ensure_index() -> None:
    if not _enabled("STARTUP_INGEST", True):
        LOGGER.info("STARTUP_INGEST disabled; skipping startup ingest")
        return

    data_dir = Path(os.getenv("DATA_DIR", "data"))
    enable_vision = _enabled("ENABLE_VISION", False)
    LOGGER.info("Ensuring Chroma index exists from %s", data_dir)
    summary = run_ingest(
        data_dir=data_dir,
        reset=False,
        skip_if_exists=True,
        enable_vision=enable_vision,
        vision_provider=os.getenv("VISION_PROVIDER"),
    )
    LOGGER.info("Startup ingest summary: %s", summary)

    if not has_data():
        raise RuntimeError("Startup ingest completed but Chroma still has no indexed data")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _ensure_index()
    mcp.run(transport="streamable-http")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
