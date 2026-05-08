from __future__ import annotations

from pathlib import Path


NOTEBOOKLM_URL = "https://notebooklm.google.com"
DEFAULT_OUTPUT_DIR = Path(".cache/task3-notebooklm")
SESSION_FILE_NAME = "session.json"
SOURCE_BUNDLE_FILE_NAME = "project-workflow-source.md"
RESULT_FILE_NAME = "notebooklm-ppt-agent-result.json"
DEFAULT_TIMEOUT_MS = 60_000
DEFAULT_SCREENSHOT_NAME = "notebooklm-ppt-current.png"

PROJECT_SOURCE_PATHS = [
    Path("plan/task.txt"),
    Path("README.md"),
    Path("plan/runtime_control.json"),
    Path("plan/progress.md"),
    Path("tests/test_output.log"),
    Path("tests/skill_execution.log"),
]

SCREENSHOT_GLOB = "tests/screenshots/*.png"

SLIDE_DECK_PROMPT = """Create a concise PowerPoint slide deck about how the EnterpriseDocMcp project was built.

Focus on:
- project goal and how Task 1, Task 2, and Task 3 relate
- Task 1 remote MCP server architecture
- Task 2 Claude Skills packaging
- Codex phase-based implementation workflow
- human-AI collaboration and feedback loop
- validation evidence: tests, logs, screenshots, deployment

Use a professional engineering presentation style.
Do not mention interviewers, hiring evaluation, or assessment criteria.
"""

UPLOAD_TEXT_CANDIDATES = ("Upload", "Upload source", "Add source")
NEW_NOTEBOOK_TEXT_CANDIDATES = ("New notebook", "Create new notebook")
SOURCE_READY_TEXT_CANDIDATES = ("Ready", "Source added", "Sources added")
GENERATE_TEXT_CANDIDATES = ("Generate", "Create", "Customize")
PRESENTATION_TEXT_CANDIDATES = ("Slide Deck", "Presentation")
DOWNLOAD_TEXT_CANDIDATES = ("Download PowerPoint", "PowerPoint", "PPTX", "Download")
