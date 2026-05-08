from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from task3_notebooklm_agent.agent import login, prepare_sources, run_agent
from task3_notebooklm_agent.config import DEFAULT_OUTPUT_DIR, DEFAULT_TIMEOUT_MS


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NotebookLM PPT browser agent for Task 3.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for source bundle, session, screenshots, and downloads.")
    parser.add_argument("--prepare-only", action="store_true", help="Only generate the NotebookLM source bundle and prompt.")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode for the upload flow.")
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS, help="Playwright timeout in milliseconds.")
    parser.add_argument("--source-file", type=Path, help="Override the source file uploaded to NotebookLM.")

    subparsers = parser.add_subparsers(dest="command")
    login_parser = subparsers.add_parser("login", help="Open NotebookLM for manual login and save browser session.")
    login_parser.add_argument("--headless", action="store_true", help="Usually false; only use for non-interactive debugging.")
    upload_parser = subparsers.add_parser("upload", help="Upload source bundle to NotebookLM and download the generated PPT.")
    upload_parser.add_argument("--source-file", type=Path, help="Override the source file uploaded to NotebookLM.")
    upload_parser.add_argument("--headless", action="store_true", help="Run upload flow headless.")
    return parser


async def _main_async(args: argparse.Namespace) -> dict:
    if args.command == "login":
        state_path = await login(args.output_dir, headless=args.headless)
        return {"status": "session_saved", "session_path": str(state_path)}

    if args.prepare_only:
        return asdict(await prepare_sources(args.output_dir))

    source_file = getattr(args, "source_file", None)
    headless = bool(getattr(args, "headless", False))
    return asdict(
        await run_agent(
            output_dir=args.output_dir,
            source_file=source_file,
            headless=headless,
            timeout_ms=args.timeout_ms,
        )
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    result = asyncio.run(_main_async(args))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
