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

from task3_notebooklm_agent.config import DEFAULT_CDP_URL, DEFAULT_OUTPUT_DIR
from task3_notebooklm_agent.mcp_agent import run_mcp_agent


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LangChain create_agent + Playwright MCP NotebookLM browser agent.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for source bundle, logs, snapshots, and result JSON.")
    parser.add_argument("--cdp-url", default=DEFAULT_CDP_URL, help="Chrome DevTools endpoint for an already-open Chrome session.")
    parser.add_argument("--model", default="openai:gpt-4.1", help="LangChain model string, e.g. openai:gpt-4.1.")
    parser.add_argument("--recursion-limit", type=int, default=80, help="Maximum LangGraph recursion/tool-call steps.")
    parser.add_argument("--max-wait-minutes", type=int, default=45, help="Maximum NotebookLM generation wait budget the browser agent should use.")
    parser.add_argument(
        "--fresh-notebook",
        action="store_true",
        help="Create a fresh NotebookLM notebook before uploading sources; use after failed generation attempts.",
    )
    parser.add_argument(
        "--outline-first",
        action="store_true",
        help="Ask NotebookLM chat for a slide outline only; do not run Slide Deck generation.",
    )
    parser.add_argument("--smoke-tools-only", action="store_true", help="Load Playwright MCP tools and exit before calling the LLM.")
    parser.add_argument(
        "--observe-existing-generation",
        action="store_true",
        help="Use the current NotebookLM page and only observe an already-started Slide Deck.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    result = asyncio.run(
        run_mcp_agent(
            output_dir=args.output_dir,
            cdp_url=args.cdp_url,
            model=args.model,
            recursion_limit=args.recursion_limit,
            smoke_tools_only=args.smoke_tools_only,
            outline_first=args.outline_first,
            observe_existing_generation=args.observe_existing_generation,
            max_wait_minutes=args.max_wait_minutes,
            fresh_notebook=args.fresh_notebook,
        )
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
