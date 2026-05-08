from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .auth import load_session, save_session
from .config import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SCREENSHOT_NAME,
    DEFAULT_TIMEOUT_MS,
    DOWNLOAD_TEXT_CANDIDATES,
    GENERATE_TEXT_CANDIDATES,
    NEW_NOTEBOOK_TEXT_CANDIDATES,
    NOTEBOOKLM_URL,
    PRESENTATION_TEXT_CANDIDATES,
    RESULT_FILE_NAME,
    SOURCE_READY_TEXT_CANDIDATES,
    UPLOAD_TEXT_CANDIDATES,
)
from .source_bundle import build_source_bundle


@dataclass(frozen=True)
class AgentResult:
    status: str
    source_path: str
    prompt_path: str
    result_path: str
    screenshot_path: str | None = None
    download_path: str | None = None
    notebook_url: str | None = None
    message: str = ""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_result(output_dir: Path, result: AgentResult) -> Path:
    path = output_dir / RESULT_FILE_NAME
    path.write_text(json.dumps(asdict(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


async def login(output_dir: Path = DEFAULT_OUTPUT_DIR, *, headless: bool = False) -> Path:
    return await save_session(output_dir, headless=headless)


async def prepare_sources(output_dir: Path = DEFAULT_OUTPUT_DIR) -> AgentResult:
    bundle = build_source_bundle(_repo_root(), output_dir)
    result = AgentResult(
        status="prepared",
        source_path=str(bundle.source_path),
        prompt_path=str(bundle.prompt_path),
        result_path=str(output_dir / RESULT_FILE_NAME),
        message=f"included={len(bundle.included_paths)} missing={len(bundle.missing_paths)}",
    )
    result_path = _write_result(output_dir, result)
    return AgentResult(**{**asdict(result), "result_path": str(result_path)})


async def _click_first_text(page, candidates: Iterable[str], *, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> str:
    last_error: Exception | None = None
    for text in candidates:
        locators = [
            page.get_by_role("button", name=re.compile(re.escape(text), re.IGNORECASE)),
            page.get_by_text(re.compile(re.escape(text), re.IGNORECASE)),
        ]
        for locator in locators:
            try:
                await locator.first.click(timeout=timeout_ms)
                return text
            except Exception as exc:  # Playwright raises several locator-specific subclasses.
                last_error = exc
    raise RuntimeError(f"Could not click any NotebookLM control matching: {', '.join(candidates)}") from last_error


async def _wait_for_any_text(page, candidates: Iterable[str], *, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> str:
    last_error: Exception | None = None
    for text in candidates:
        try:
            await page.get_by_text(re.compile(re.escape(text), re.IGNORECASE)).first.wait_for(timeout=timeout_ms)
            return text
        except Exception as exc:
            last_error = exc
    raise TimeoutError(f"NotebookLM did not show any expected text: {', '.join(candidates)}") from last_error


async def run_agent(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    source_file: Path | None = None,
    headless: bool = True,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> AgentResult:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    prepared = await prepare_sources(output_dir)
    upload_path = (source_file or Path(prepared.source_path)).resolve()
    if not upload_path.exists():
        raise FileNotFoundError(f"Source file not found: {upload_path}")

    screenshot_path = output_dir / DEFAULT_SCREENSHOT_NAME
    browser = None
    async with async_playwright() as playwright:
        browser, context = await load_session(playwright, output_dir, headless=headless, timeout_ms=timeout_ms)
        page = await context.new_page()
        try:
            await page.goto(NOTEBOOKLM_URL)
            await page.wait_for_load_state("domcontentloaded")
            await _click_first_text(page, NEW_NOTEBOOK_TEXT_CANDIDATES)

            try:
                async with page.expect_file_chooser(timeout=timeout_ms) as chooser_info:
                    await _click_first_text(page, UPLOAD_TEXT_CANDIDATES, timeout_ms=3_000)
                chooser = await chooser_info.value
                await chooser.set_files(str(upload_path))
            except Exception:
                await page.wait_for_timeout(3_000)
                async with page.expect_file_chooser(timeout=timeout_ms) as chooser_info:
                    await _click_first_text(page, UPLOAD_TEXT_CANDIDATES, timeout_ms=timeout_ms)
                chooser = await chooser_info.value
                await chooser.set_files(str(upload_path))

            await _wait_for_any_text(page, SOURCE_READY_TEXT_CANDIDATES, timeout_ms=timeout_ms)
            await _click_first_text(page, GENERATE_TEXT_CANDIDATES)
            await _click_first_text(page, PRESENTATION_TEXT_CANDIDATES)

            try:
                async with page.expect_download(timeout=timeout_ms) as download_info:
                    await _click_first_text(page, DOWNLOAD_TEXT_CANDIDATES)
                download = await download_info.value
                save_path = output_dir / download.suggested_filename
                await download.save_as(str(save_path))
                status = "completed"
                message = "NotebookLM PPTX downloaded"
                download_path = str(save_path)
            except PlaywrightTimeoutError as exc:
                status = "manual_download_required"
                message = f"Download did not start automatically: {exc}"
                download_path = None

            await page.screenshot(path=str(screenshot_path), full_page=True)
            result = AgentResult(
                status=status,
                source_path=prepared.source_path,
                prompt_path=prepared.prompt_path,
                result_path=str(output_dir / RESULT_FILE_NAME),
                screenshot_path=str(screenshot_path),
                download_path=download_path,
                notebook_url=page.url,
                message=message,
            )
            result_path = _write_result(output_dir, result)
            return AgentResult(**{**asdict(result), "result_path": str(result_path)})
        finally:
            if browser is not None and headless:
                await browser.close()
