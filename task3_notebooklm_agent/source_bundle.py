from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config import NOTEBOOKLM_SCREENSHOT_GLOB, PROJECT_SOURCE_PATHS, SLIDE_DECK_PROMPT


SENSITIVE_LINE_RE = re.compile(r"(?im)^(.*(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*=\s*).*$")


@dataclass(frozen=True)
class ProjectSignals:
    task1_title: str
    task2_title: str
    task3_title: str
    current_phase: str
    completed_phases: int
    validation_themes: list[str]


@dataclass(frozen=True)
class SourceBundleResult:
    source_path: Path
    upload_path: Path
    prompt_path: Path
    screenshot_paths: list[Path]
    included_paths: list[Path]
    missing_paths: list[Path]


def _has_redacted_credentials(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return bool(SENSITIVE_LINE_RE.search(text))


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return SENSITIVE_LINE_RE.sub(r"\1[redacted]", text)


def _extract_task_title(task_text: str, task_number: int, fallback: str) -> str:
    pattern = re.compile(rf"(?im)^\s*(?:#{1,4}\s*)?Task\s*{task_number}\s*[:：-]?\s*(.+?)\s*$")
    match = pattern.search(task_text)
    if not match:
        return fallback
    title = match.group(1).strip()
    return title or fallback


def _load_runtime_signals(runtime_text: str) -> tuple[str, int, list[str]]:
    try:
        data = json.loads(runtime_text)
    except json.JSONDecodeError:
        return "unknown", 0, []

    phases = data.get("phases", [])
    current_phase = str(data.get("current_phase", "unknown"))
    completed = sum(1 for phase in phases if phase.get("status") == "completed")
    validation: list[str] = []
    for phase in phases:
        notes = phase.get("implementation_check", {}).get("notes", "")
        if notes and any(word in notes.lower() for word in ("test", "validation", "passed", "health", "py_compile")):
            validation.append(str(notes))
    return current_phase, completed, validation[-5:]


def _collect_project_signals(repo_root: Path) -> ProjectSignals:
    task_text = _read(repo_root / "plan/task.txt")
    runtime_text = _read(repo_root / "plan/runtime_control.json")
    current_phase, completed, validation = _load_runtime_signals(runtime_text)
    return ProjectSignals(
        task1_title=_extract_task_title(task_text, 1, "Remote MCP Server"),
        task2_title=_extract_task_title(task_text, 2, "Claude Skills Packaging"),
        task3_title=_extract_task_title(task_text, 3, "NotebookLM Browser Agent"),
        current_phase=current_phase,
        completed_phases=completed,
        validation_themes=validation,
    )


def _bullets(items: list[str], *, fallback: str, limit: int = 4) -> list[str]:
    selected = [item for item in items if item][:limit]
    if not selected:
        selected = [fallback]
    return [f"- {item}" for item in selected]


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
    signals = _collect_project_signals(repo_root)

    sections = [
        "# EnterpriseDocMcp Implementation Workflow",
        "",
        "This is a curated source for a NotebookLM Slide Deck. It contains only presentation material, not prompts, raw logs, runtime JSON, credentials, browser state, or implementation transcripts.",
        "",
        "## Executive Summary",
        "",
        f"EnterpriseDocMcp is an engineering project that converts enterprise documents into an AI-ready knowledge workflow. The work is currently tracked at {signals.current_phase}, with {signals.completed_phases} completed phases recorded in runtime control. The system parses documents, indexes them for retrieval, exposes search through a remote MCP server, packages preprocessing workflows as Claude Skills, and uses a browser agent to generate NotebookLM presentation evidence. The project emphasizes traceable phase execution, repeatable validation, and disciplined human-AI collaboration.",
        "",
        f"## Task 1: {signals.task1_title}",
        "",
        "Task 1 delivers the core document intelligence service. It includes parsing modules for text, tables, rendered pages, vision-assisted analysis, PDF files, and PowerPoint files. Parsed records are chunked, embedded, stored in Chroma, and retrieved through search tools. The MCP server exposes document search, source-specific search, and document listing capabilities so external AI tools can query the indexed enterprise knowledge base. Deployment is packaged with Docker and validated with server health checks and MCP client smoke tests.",
        "",
        "Key points for the deck:",
        "- Converts unstructured enterprise files into searchable chunks.",
        "- Uses parsing, chunking, embeddings, vector storage, reranking, and retrieval evaluation.",
        "- Exposes capabilities through a FastMCP server.",
        "- Supports local and deployment validation through tests, health checks, and client calls.",
        "",
        f"## Task 2: {signals.task2_title}",
        "",
        "Task 2 turns the preprocessing workflow into reusable Claude Skills. The parse Skill handles enterprise document parsing with clear input and output expectations. The index Skill wraps ingestion and indexing commands with directory aliases and safe execution boundaries. The Skills include direct command examples, script references, fixture-based validation, and rules that prevent unsafe or unnecessary execution.",
        "",
        "Key points for the deck:",
        "- Packages parsing and indexing as reusable AI-callable workflows.",
        "- Documents safe boundaries, commands, inputs, and outputs.",
        "- Uses fixture inputs and unit tests as verification evidence.",
        "- Keeps Task 2 distinct from the remote MCP server in Task 1.",
        "",
        f"## Task 3: {signals.task3_title}",
        "",
        "Task 3 automates NotebookLM through a real browser workflow. The final design uses LangChain create_agent with Microsoft Playwright MCP browser tools connected to an already-authenticated Chrome session through CDP. The browser agent uploads a curated project source, optionally uses NotebookLM chat to produce an outline first, then triggers NotebookLM Slide Deck generation. Success is accepted when the browser workflow reaches source upload plus Slide Deck generation evidence in logs, screenshots, snapshots, and result JSON.",
        "",
        "Key points for the deck:",
        "- Uses a real NotebookLM UI workflow rather than fabricating slides locally.",
        "- Uses Playwright MCP tools instead of brittle selector-only browser code.",
        "- Avoids repeated generation attempts because NotebookLM Slide Deck is a beta feature.",
        "- Records output logs, upload manifests, screenshots, snapshots, and result JSON.",
        "",
        "## Phase-Based Engineering Workflow",
        "",
        "The project is managed through explicit phase files and runtime control metadata. Each phase defines scoped work, required paths, validation commands, status, notes, and commit gates. The workflow requires validation before completion and prohibits automatic commits. Progress is recorded in a human-readable progress log so the implementation history remains auditable.",
        "",
        "Key points for the deck:",
        "- Each phase has a bounded implementation scope.",
        "- Validation commands are part of the contract, not an afterthought.",
        "- Blocked states are recorded when external systems fail or evidence is incomplete.",
        "- User approval is required before commits.",
        "",
        "## Human-AI Collaboration",
        "",
        "The implementation improved through direct human feedback. The user identified that the first browser approach stalled in the operating system file manager, that committing before evidence would be wrong, and that repeated Slide Deck generation wastes limited NotebookLM attempts. These corrections shifted the design toward a stricter MCP browser agent, cleaner source generation, single-generation rules, bounded waiting, and an outline-first safety mode.",
        "",
        "Key points for the deck:",
        "- Human review caught false completion and incorrect automation assumptions.",
        "- Browser automation was simplified to one official MCP path.",
        "- Source content was curated to avoid prompts, logs, and irrelevant screenshots.",
        "- Evidence gates prevented incomplete Task 3 completion.",
        "",
        "## Validation Evidence",
        "",
        "Validation combines automated checks and external workflow evidence. Automated checks include unit tests, py_compile, CLI help checks, JSON validation, Docker smoke tests, MCP client checks, and Skill execution tests. External NotebookLM evidence requires a run log, upload manifest, result JSON, and screenshot or snapshot evidence that source upload and Slide Deck generation were actually driven in the browser.",
        "",
        "Key points for the deck:",
        *_bullets(
            signals.validation_themes,
            fallback="Unit tests, CLI smoke tests, JSON validation, and py_compile checks provide implementation evidence.",
            limit=4,
        ),
    ]

    for relative_path in paths:
        if (repo_root / relative_path).exists():
            included.append(relative_path)
        else:
            missing.append(relative_path)

    screenshot_paths = sorted(repo_root.glob(NOTEBOOKLM_SCREENSHOT_GLOB))
    if screenshot_paths:
        sections.extend(["## Screenshot Evidence Index", ""])
        for screenshot in screenshot_paths:
            sections.append(f"- {screenshot.relative_to(repo_root).as_posix()}")
        sections.append("")

    source_path = output_dir / "project-workflow-source.md"
    upload_path = output_dir / "project-workflow-source.txt"
    prompt_path = output_dir / "notebooklm-slide-deck-prompt.txt"
    source_text = "\n".join(sections)
    source_path.write_text(source_text, encoding="utf-8")
    upload_path.write_text(source_text, encoding="utf-8")
    prompt_path.write_text(SLIDE_DECK_PROMPT.strip() + "\n", encoding="utf-8")
    return SourceBundleResult(source_path, upload_path, prompt_path, screenshot_paths, included, missing)
