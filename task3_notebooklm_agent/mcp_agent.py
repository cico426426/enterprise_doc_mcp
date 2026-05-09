from __future__ import annotations

import json
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import DEFAULT_CDP_URL, DEFAULT_OUTPUT_DIR, RESULT_FILE_NAME, SLIDE_DECK_PROMPT
from .source_bundle import build_source_bundle
from dotenv import load_dotenv

load_dotenv()

MCP_AGENT_LOG_NAME = "notebooklm-ppt-mcp-agent.log"
MCP_UPLOAD_MANIFEST_NAME = "notebooklm-upload-manifest.json"
MCP_OUTLINE_NAME = "notebooklm-slide-outline.md"


@dataclass(frozen=True)
class MCPAgentResult:
    status: str
    source_path: str
    prompt_path: str
    result_path: str
    log_path: str
    manifest_path: str
    outline_path: str | None = None
    message: str = ""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _message_to_log_line(message: Any) -> str:
    msg_type = getattr(message, "type", message.__class__.__name__)
    name = getattr(message, "name", None)
    content = getattr(message, "content", "")
    if isinstance(content, list):
        content = json.dumps(content, ensure_ascii=False)
    prefix = f"{msg_type}"
    if name:
        prefix += f"[{name}]"
    return f"{prefix}: {content}"


def _message_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content)


def _latest_assistant_text(messages: list[Any]) -> str:
    for message in reversed(messages):
        if getattr(message, "type", "") == "ai":
            text = _message_text(message).strip()
            if text:
                return text
    return ""


def _latest_snapshot_text(output_dir: Path) -> str:
    snapshots = sorted(output_dir.glob("*.yml"), key=lambda path: path.stat().st_mtime, reverse=True)
    for snapshot in snapshots:
        text = snapshot.read_text(encoding="utf-8", errors="replace")
        if text.strip():
            return text
    return ""


def _snapshot_shows_slide_deck_workflow(text: str) -> bool:
    signals = (
        "正在生成簡報",
        "開始生成「簡報」",
        "Start slideshow",
        "View custom prompt",
        "Good content",
        "開始投影片放映",
    )
    return any(signal in text for signal in signals)


def _assistant_reported_blocked(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized.startswith("blocked") or "status=blocked" in normalized or "report blocked" in normalized


def _write_upload_manifest(path: Path, *, source_path: Path, prompt_path: Path, image_paths: list[Path]) -> None:
    _write_json(
        path,
        {
            "primary_text_source": str(source_path),
            "prompt_path": str(prompt_path),
            "optional_image_sources": [str(image_path) for image_path in image_paths],
            "upload_guidance": (
                "Use the concise text brief as the required source. "
                "Only upload NotebookLM-specific screenshot evidence when it directly helps the final deck. "
                "Do not upload unrelated Task 2 skill screenshots."
            ),
        },
    )


def _recoverable_tool_error(exc: Exception) -> str:
    return (
        "Tool call failed but the agent can recover. "
        f"Error: {type(exc).__name__}: {exc}. "
        "Inspect the current browser snapshot and choose the next UI action. "
        "For browser_file_upload specifically, first click the NotebookLM local upload/from-computer control "
        "so Playwright MCP has file chooser modal state, then call browser_file_upload."
    )


def _format_exception(exc: BaseException) -> str:
    lines = [f"{type(exc).__name__}: {exc}"]
    if isinstance(exc, BaseExceptionGroup):
        for index, sub_exc in enumerate(exc.exceptions, start=1):
            lines.append(f"sub-exception {index}: {type(sub_exc).__name__}: {sub_exc}")
            lines.extend(traceback.format_exception(type(sub_exc), sub_exc, sub_exc.__traceback__))
    else:
        lines.extend(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return "".join(lines)


def _build_user_prompt(
    source_path: Path,
    output_dir: Path,
    *,
    image_paths: list[Path] | None = None,
    outline_first: bool = False,
    observe_existing_generation: bool = False,
    max_wait_minutes: int = 45,
    fresh_notebook: bool = False,
) -> str:
    image_paths = image_paths or []
    image_section = "\n".join(f"- {path}" for path in image_paths) or "- None found."
    if observe_existing_generation:
        return f"""
Drive NotebookLM in the browser using the available Playwright MCP tools.

Goal:
Observe an already-started NotebookLM Slide Deck run and capture browser evidence.

Current state assumption:
The source has already been uploaded and the Slide Deck/簡報 generation button has already been clicked.

Required workflow:
1. Inspect the current page with the browser snapshot.
2. Stay in the current NotebookLM notebook. Do not navigate to the NotebookLM home/list page.
3. Do not upload another source file.
4. Do not click Generate, create a new Slide Deck, or retry generation. This mode is observation-only.
5. Capture the current browser snapshot and report the visible Slide Deck state.
6. If the snapshot shows 正在生成簡報, 開始生成「簡報」, Start slideshow, View custom prompt, Good content, 開始投影片放映, or a visible generated deck, immediately report generation_started or completed_browser_workflow and stop.

Waiting policy:
- Do not poll for completion in observation mode.
- Do not wait for NotebookLM to finish rendering the deck.
- If the current snapshot does not show generated or generating Slide Deck state, report blocked and describe the visible state exactly.

Hard gates:
- Do not ask the user whether to continue waiting.
- Stop immediately after the first snapshot that shows Slide Deck generation was started or completed. Do not wait for completion, export, sharing, or additional readiness controls.
- If the current page is not already inside a NotebookLM notebook, report blocked. Do not navigate to find a notebook.
- If there is no existing generated or generating Slide Deck, report blocked. Do not start a new generation in observation mode.
- If a UI label is different, use snapshots to reason from the available controls.
"""

    notebook_instruction = (
        "Navigate to the NotebookLM home/list page and create a fresh new notebook before uploading sources. "
        "Do not reuse the current notebook because it may contain failed generation attempts."
        if fresh_notebook
        else "If you are on the NotebookLM home/list page, create a new notebook. If you are already inside a notebook, use it."
    )

    if outline_first:
        return f"""
Drive NotebookLM in the browser using the available Playwright MCP tools.

Goal:
Validate that NotebookLM can understand the source by generating a slide outline in chat. Do not use the Slide Deck/簡報 Studio tool in this mode.

Required primary text source:
{source_path}

Optional image evidence sources:
{image_section}

Required workflow:
1. Inspect the current page with the browser snapshot.
2. Notebook selection: {notebook_instruction}
3. Decide what to upload:
   - Always upload the required primary text source first because it contains the curated slide narrative.
   - Optional images are candidates only. Upload them only if they are NotebookLM-specific evidence and directly help the final deck.
   - Do not upload unrelated skill screenshots or images just because they are listed.
4. Add/upload all selected sources from the local computer and wait until the source list is stable.
5. In the NotebookLM chat box, ask exactly this request:
請根據目前所有來源，整理一份 6-8 頁的 PowerPoint 簡報大綱。每頁請提供：投影片標題、3-5 個重點 bullet、建議視覺元素、30-60 秒講稿。主題是 EnterpriseDocMcp 的實作流程、Task 1 MCP Server、Task 2 Claude Skills、Task 3 NotebookLM Browser Agent、phase-based validation 與人機協作。請不要提到面試、評審或招聘情境。
6. Wait for the chat answer to complete.
7. Return the generated outline content in your final response.

Strict prohibitions:
- Do not click Slide Deck/簡報.
- Do not open Studio customization.
- Do not click Generate.
- If NotebookLM chat cannot produce an outline, report blocked and explain the visible error.
"""

    return f"""
Drive NotebookLM in the browser using the available Playwright MCP tools.

Goal:
Generate a NotebookLM Slide Deck from this local source file and capture browser evidence.

Required primary text source:
{source_path}

Optional image evidence sources:
{image_section}

Required workflow:
1. Inspect the current page with the browser snapshot.
2. Notebook selection: {notebook_instruction}
3. Decide what to upload:
   - Always upload the required primary text source first because it contains the curated slide narrative.
   - Optional images are candidates only. Upload them only if they are NotebookLM-specific evidence and directly help the final deck.
   - Do not upload unrelated skill screenshots or images just because they are listed.
   - Do not upload browser session files, caches, credentials, or unrelated repository files.
4. Add/upload all selected sources from the local computer before generating:
   - First click NotebookLM's Add source / Upload / From your computer UI control.
   - Only after the click opens a file chooser/modal state, call browser_file_upload with the selected local file path or paths.
   - Do not call browser_file_upload before opening the file chooser; Playwright MCP rejects that.
   - If images are selected, upload them before opening Studio or generating the Slide Deck.
5. Wait until NotebookLM has processed every selected source and the source list is stable.
6. Before generating, verify that no additional sources still need to be uploaded. Once generation starts, do not upload any more sources.
7. In the Studio panel, choose Slide Deck. If a customization prompt is available, use this prompt:
{SLIDE_DECK_PROMPT}
8. Click Generate exactly once. Do not click Generate again in this run.
9. Immediately capture a browser snapshot after clicking Generate.
10. If the snapshot shows 正在生成簡報, 開始生成「簡報」, or any generated Slide Deck UI, report generation_started or completed_browser_workflow and stop. Do not wait for the deck to finish.

Waiting policy:
- Use at most one short browser_wait_for after clicking Generate if the UI needs a moment to show the generating state.
- Do not poll for completion.
- Do not wait for NotebookLM to finish rendering the deck.

Hard gates:
- Generate exactly once at most. If NotebookLM says it cannot generate the Slide Deck, report blocked and stop; do not upload more sources and do not retry Generate.
- After Generate has been clicked, do not add sources in the same notebook during this run.
- Do not ask the user whether to continue waiting.
- Stop immediately after the first snapshot that shows Slide Deck generation was started or completed. Do not wait for completion, export, sharing, or additional readiness controls.
- If a UI label is different, use snapshots to reason from the available controls.
"""


async def run_mcp_agent(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    cdp_url: str = DEFAULT_CDP_URL,
    model: str = "openai:gpt-4.1",
    recursion_limit: int = 80,
    smoke_tools_only: bool = False,
    outline_first: bool = False,
    observe_existing_generation: bool = False,
    max_wait_minutes: int = 45,
    fresh_notebook: bool = False,
) -> MCPAgentResult:
    from langchain.agents import create_agent
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_mcp_adapters.tools import load_mcp_tools

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_source_bundle(_repo_root(), output_dir)
    source_path = bundle.upload_path.resolve()
    prompt_path = bundle.prompt_path.resolve()
    image_paths = [path.resolve() for path in bundle.screenshot_paths]
    log_path = output_dir / MCP_AGENT_LOG_NAME
    manifest_path = output_dir / MCP_UPLOAD_MANIFEST_NAME
    outline_path = output_dir / MCP_OUTLINE_NAME
    result_path = output_dir / RESULT_FILE_NAME
    _write_upload_manifest(manifest_path, source_path=source_path, prompt_path=prompt_path, image_paths=image_paths)

    client = MultiServerMCPClient(
        {
            "playwright": {
                "transport": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@playwright/mcp@latest",
                    "--cdp-endpoint",
                    cdp_url,
                    "--output-dir",
                    str(output_dir.resolve()),
                    "--timeout-action",
                    "10000",
                    "--timeout-navigation",
                    "120000",
                ],
            }
        }
    )

    lines = [
        "NotebookLM Playwright MCP Agent",
        f"model={model}",
        f"cdp_url={cdp_url}",
        f"source_path={source_path}",
        f"prompt_path={prompt_path}",
        f"manifest_path={manifest_path.resolve()}",
        "optional_image_sources=" + ", ".join(str(path) for path in image_paths),
        f"output_dir={output_dir.resolve()}",
        f"outline_first={outline_first}",
        f"observe_existing_generation={observe_existing_generation}",
        f"max_wait_minutes={max_wait_minutes}",
        f"fresh_notebook={fresh_notebook}",
        "",
    ]

    try:
        async with client.session("playwright") as session:
            tools = await load_mcp_tools(session)
            for tool in tools:
                tool.handle_tool_error = _recoverable_tool_error
                tool.handle_validation_error = (
                    "Tool input validation failed. Inspect the browser snapshot and retry with valid arguments."
                )
            lines.append("loaded_tools=" + ", ".join(sorted(tool.name for tool in tools)))
            if smoke_tools_only:
                lines.append("smoke_tools_only=true")
                lines.append("MCP tool loading succeeded; skipped LLM browser workflow")
                log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                result = MCPAgentResult(
                    status="prepared",
                    source_path=str(source_path),
                    prompt_path=str(prompt_path),
                    result_path=str(result_path),
                    log_path=str(log_path),
                    manifest_path=str(manifest_path),
                    outline_path=str(outline_path),
                    message="MCP tool loading succeeded; skipped LLM browser workflow",
                )
                _write_json(result_path, asdict(result))
                return result
            agent = create_agent(
                model,
                tools,
                system_prompt=(
                    "You are a browser automation agent. Use Playwright MCP tools only for browser work. "
                    "Be explicit and persistent. Do not ask the user for permission to keep waiting. "
                    "Stop immediately when a snapshot shows Slide Deck generation was started or completed. "
                    "Do not wait for completion, export, sharing, or additional readiness controls."
                ),
            )
            response = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": _build_user_prompt(
                                source_path,
                                output_dir.resolve(),
                                image_paths=image_paths,
                                outline_first=outline_first,
                                observe_existing_generation=observe_existing_generation,
                                max_wait_minutes=max_wait_minutes,
                                fresh_notebook=fresh_notebook,
                            ),
                        }
                    ]
                },
                {"recursion_limit": recursion_limit},
            )
    except Exception as exc:
        snapshot_text = _latest_snapshot_text(output_dir)
        if _snapshot_shows_slide_deck_workflow(snapshot_text):
            message = (
                f"MCP browser workflow reached NotebookLM Slide Deck generation state before the agent stopped: "
                f"{type(exc).__name__}: {exc}"
            )
            lines.append(message)
            lines.append(_format_exception(exc))
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = MCPAgentResult(
                status="generation_started",
                source_path=str(source_path),
                prompt_path=str(prompt_path),
                result_path=str(result_path),
                log_path=str(log_path),
                manifest_path=str(manifest_path),
                outline_path=str(outline_path) if outline_path.exists() else None,
                message=message,
            )
            _write_json(result_path, asdict(result))
            return result

        message = f"MCP browser agent failed: {type(exc).__name__}: {exc}"
        lines.append(message)
        lines.append(_format_exception(exc))
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = MCPAgentResult(
            status="failed",
            source_path=str(source_path),
            prompt_path=str(prompt_path),
            result_path=str(result_path),
            log_path=str(log_path),
            manifest_path=str(manifest_path),
            outline_path=str(outline_path) if outline_path.exists() else None,
            message=message,
        )
        _write_json(result_path, asdict(result))
        return result

    for message in response.get("messages", []):
        lines.append(_message_to_log_line(message))

    assistant_text = _latest_assistant_text(response.get("messages", []))
    if outline_first:
        outline_text = assistant_text
        if outline_text:
            outline_path.write_text(outline_text.rstrip() + "\n", encoding="utf-8")
            status = "outline_completed"
            message = "NotebookLM chat outline captured; Slide Deck generation intentionally skipped"
        else:
            status = "blocked"
            message = "Outline-first run finished without a captured outline"
        lines.append("")
        lines.append(f"status={status}")
        lines.append(f"outline_path={outline_path if outline_path.exists() else None}")
        lines.append(f"message={message}")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = MCPAgentResult(
            status=status,
            source_path=str(source_path),
            prompt_path=str(prompt_path),
            result_path=str(result_path),
            log_path=str(log_path),
            manifest_path=str(manifest_path),
            outline_path=str(outline_path) if outline_path.exists() else None,
            message=message,
        )
        _write_json(result_path, asdict(result))
        return result

    snapshot_text = _latest_snapshot_text(output_dir)
    if _assistant_reported_blocked(assistant_text):
        status = "blocked"
        message = "MCP agent reported blocked before Slide Deck generation evidence"
    elif _snapshot_shows_slide_deck_workflow(snapshot_text):
        status = "generation_started"
        message = "MCP browser workflow reached NotebookLM Slide Deck generation state"
    else:
        status = "blocked"
        message = "MCP agent finished without NotebookLM Slide Deck workflow evidence"

    lines.append("")
    lines.append(f"status={status}")
    lines.append(f"message={message}")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = MCPAgentResult(
        status=status,
        source_path=str(source_path),
        prompt_path=str(prompt_path),
        result_path=str(result_path),
        log_path=str(log_path),
        manifest_path=str(manifest_path),
        outline_path=str(outline_path) if outline_path.exists() else None,
        message=message,
    )
    _write_json(result_path, asdict(result))
    return result
