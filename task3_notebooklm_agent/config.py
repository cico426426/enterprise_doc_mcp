from __future__ import annotations

from pathlib import Path


DEFAULT_OUTPUT_DIR = Path(".cache/task3-notebooklm")
RESULT_FILE_NAME = "notebooklm-ppt-agent-result.json"
DEFAULT_CDP_URL = "http://127.0.0.1:9222"

PROJECT_SOURCE_PATHS = [
    Path("plan/task.txt"),
    Path("README.md"),
    Path("plan/runtime_control.json"),
    Path("plan/progress.md"),
    Path("tests/test_output.log"),
    Path("tests/skill_execution.log"),
]

NOTEBOOKLM_SCREENSHOT_GLOB = "tests/screenshots/notebooklm-ppt-*.png"

SLIDE_DECK_PROMPT = """請使用繁體中文建立一份精簡、專業的 PowerPoint 簡報，說明 EnterpriseDocMcp 專案是如何被實作完成的。

請聚焦在：
- 專案目標，以及 Task 1、Task 2、Task 3 之間的關係
- Task 1 Remote MCP Server 架構
- Task 2 Claude Skills 封裝
- Codex phase-based implementation workflow
- 人機協作與 feedback loop
- 驗證證據：tests、logs、screenshots、deployment

請使用工程專案簡報風格，標題與內文都使用繁體中文。
"""

SLIDE_DECK_READY_TEXT_CANDIDATES = (
    "Start slideshow",
    "View custom prompt",
    "Good content",
    "開始投影片放映",
)
