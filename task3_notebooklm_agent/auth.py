from __future__ import annotations

from pathlib import Path

from .config import DEFAULT_TIMEOUT_MS, NOTEBOOKLM_URL, SESSION_FILE_NAME


def session_path(output_dir: Path) -> Path:
    return output_dir / SESSION_FILE_NAME


async def save_session(output_dir: Path, *, headless: bool = False, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> Path:
    from playwright.async_api import async_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = session_path(output_dir)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context()
        context.set_default_timeout(timeout_ms)
        page = await context.new_page()
        await page.goto(NOTEBOOKLM_URL)
        print("Log in to NotebookLM in the browser window, then press Enter here.")
        input()
        await context.storage_state(path=str(state_path))
        await browser.close()
    return state_path


async def load_session(playwright, output_dir: Path, *, headless: bool, timeout_ms: int = DEFAULT_TIMEOUT_MS):
    state_path = session_path(output_dir)
    if not state_path.exists():
        raise FileNotFoundError(
            f"NotebookLM session not found at {state_path}. "
            "Run `uv run python scripts/notebooklm_ppt_agent.py login` first."
        )
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context(storage_state=str(state_path), accept_downloads=True)
    context.set_default_timeout(timeout_ms)
    return browser, context
