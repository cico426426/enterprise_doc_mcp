from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config import PROJECT_SOURCE_PATHS, SCREENSHOT_GLOB, SLIDE_DECK_PROMPT


MAX_SECTION_CHARS = 12_000
SENSITIVE_LINE_RE = re.compile(r"(?im)^(.*(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*=\s*).*$")


@dataclass(frozen=True)
class SourceBundleResult:
    source_path: Path
    prompt_path: Path
    included_paths: list[Path]
    missing_paths: list[Path]


def _read_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = SENSITIVE_LINE_RE.sub(r"\1[redacted]", text)
    if len(text) <= MAX_SECTION_CHARS:
        return text
    return text[:MAX_SECTION_CHARS] + "\n\n[truncated for NotebookLM source bundle]\n"


def _summarize_runtime_control(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text

    current = data.get("current_phase", "unknown")
    phases = data.get("phases", [])
    compact = [
        {
            "id": phase.get("id"),
            "title": phase.get("title"),
            "status": phase.get("status"),
            "notes": phase.get("implementation_check", {}).get("notes", ""),
        }
        for phase in phases
    ]
    return json.dumps({"current_phase": current, "phases": compact}, indent=2, ensure_ascii=False)


def build_source_bundle(
    repo_root: Path,
    output_dir: Path,
    *,
    source_paths: list[Path] | None = None,
) -> SourceBundleResult:
    repo_root = repo_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = source_paths or PROJECT_SOURCE_PATHS
    included: list[Path] = []
    missing: list[Path] = []

    sections = [
        "# EnterpriseDocMcp Project Workflow Source",
        "",
        "This source bundle is generated from public repository files for NotebookLM.",
        "It excludes credentials, local caches, browser sessions, and private environment files.",
        "",
        "## Intended Slide Deck Prompt",
        "",
        SLIDE_DECK_PROMPT.strip(),
        "",
    ]

    for relative_path in paths:
        path = repo_root / relative_path
        if not path.exists():
            missing.append(relative_path)
            continue
        included.append(relative_path)
        text = _read_text(path)
        if relative_path == Path("plan/runtime_control.json"):
            text = _summarize_runtime_control(text)
        sections.extend(
            [
                f"## Source: {relative_path.as_posix()}",
                "",
                "```text",
                text.strip(),
                "```",
                "",
            ]
        )

    screenshot_paths = sorted(repo_root.glob(SCREENSHOT_GLOB))
    if screenshot_paths:
        sections.extend(["## Screenshot Evidence Index", ""])
        for screenshot in screenshot_paths:
            sections.append(f"- {screenshot.relative_to(repo_root).as_posix()}")
        sections.append("")

    source_path = output_dir / "project-workflow-source.md"
    prompt_path = output_dir / "notebooklm-slide-deck-prompt.txt"
    source_path.write_text("\n".join(sections), encoding="utf-8")
    prompt_path.write_text(SLIDE_DECK_PROMPT.strip() + "\n", encoding="utf-8")
    return SourceBundleResult(source_path, prompt_path, included, missing)
