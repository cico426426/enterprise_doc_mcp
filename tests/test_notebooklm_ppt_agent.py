from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from task3_notebooklm_agent.config import SLIDE_DECK_PROMPT, SLIDE_DECK_READY_TEXT_CANDIDATES
from task3_notebooklm_agent.mcp_agent import _assistant_reported_blocked, _build_user_prompt, _snapshot_shows_slide_deck_workflow
from task3_notebooklm_agent.source_bundle import build_source_bundle


ROOT = Path(__file__).resolve().parents[1]


class SourceBundleTests(unittest.TestCase):
    def test_build_source_bundle_uses_public_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = build_source_bundle(ROOT, Path(tmp))

            self.assertTrue(result.source_path.exists())
            self.assertTrue(result.upload_path.exists())
            self.assertTrue(result.prompt_path.exists())
            self.assertIsInstance(result.screenshot_paths, list)
            body = result.source_path.read_text(encoding="utf-8")
            upload_body = result.upload_path.read_text(encoding="utf-8")

        self.assertIn("EnterpriseDocMcp Implementation Workflow", body)
        self.assertEqual(body, upload_body)
        self.assertIn("Task 1: Remote MCP Server", body)
        self.assertIn("Task 2: Claude Skills Packaging", body)
        self.assertIn("Task 3: NotebookLM Browser Agent", body)
        self.assertIn("Human-AI Collaboration", body)
        self.assertIn("Slide Deck", body)
        self.assertNotIn("Current Task 3 Risk", body)
        self.assertNotIn("Security Note", body)
        self.assertNotIn("Intended Slide Deck Prompt", body)
        self.assertNotIn("Do not mention interviewers", body)
        self.assertNotIn("Recent Progress Signals", body)
        self.assertNotIn("Blocked State", body)
        self.assertNotIn("phase-17 blocked", body)
        self.assertNotIn("Evidence Excerpt:", body)
        self.assertNotIn("OPENAI_API_KEY=...", body)
        self.assertNotIn("ANTHROPIC_API_KEY=...", body)
        self.assertLess(len(body), 10_000)
        self.assertNotIn("index-enterprise-documents-skills.png", body)

    def test_prompt_mentions_required_deck_content(self) -> None:
        self.assertIn("繁體中文", SLIDE_DECK_PROMPT)
        self.assertIn("Task 1", SLIDE_DECK_PROMPT)
        self.assertIn("Task 2", SLIDE_DECK_PROMPT)
        self.assertIn("Task 3", SLIDE_DECK_PROMPT)
        self.assertIn("Claude Skills", SLIDE_DECK_PROMPT)
        self.assertNotIn("面試官", SLIDE_DECK_PROMPT)
        self.assertNotIn("招聘", SLIDE_DECK_PROMPT)
        self.assertNotIn("考核", SLIDE_DECK_PROMPT)


class AgentUploadTests(unittest.TestCase):
    def test_slide_deck_generation_evidence_is_the_hard_gate(self) -> None:
        self.assertIn("Start slideshow", SLIDE_DECK_READY_TEXT_CANDIDATES)
        self.assertNotIn("Download", SLIDE_DECK_READY_TEXT_CANDIDATES)

    def test_mcp_agent_prompt_requires_one_shot_generation(self) -> None:
        prompt = _build_user_prompt(
            Path("/tmp/source.txt"),
            Path("/tmp/out"),
            image_paths=[Path("/tmp/screenshot.png")],
            max_wait_minutes=30,
        )

        self.assertIn("Playwright MCP tools", prompt)
        self.assertIn("Decide what to upload", prompt)
        self.assertIn("Click Generate exactly once", prompt)
        self.assertIn("If NotebookLM says it cannot generate", prompt)
        self.assertIn("Do not upload unrelated skill screenshots", prompt)
        self.assertIn("/tmp/screenshot.png", prompt)
        self.assertIn("capture browser evidence", prompt)
        self.assertNotIn("download", prompt.lower())
        self.assertIn("Do not call browser_file_upload before opening the file chooser", prompt)
        self.assertIn("Do not ask the user whether to continue waiting", prompt)
        self.assertIn("Immediately capture a browser snapshot after clicking Generate", prompt)
        self.assertIn("Do not poll for completion", prompt)
        self.assertIn("Do not wait for completion", prompt)
        self.assertIn("Use at most one short browser_wait_for", prompt)

    def test_mcp_agent_observation_prompt_skips_reupload(self) -> None:
        prompt = _build_user_prompt(
            Path("/tmp/source.txt"),
            Path("/tmp/out"),
            observe_existing_generation=True,
            max_wait_minutes=60,
        )

        self.assertIn("Observe an already-started NotebookLM Slide Deck run", prompt)
        self.assertIn("Do not upload another source file", prompt)
        self.assertIn("observation-only", prompt)
        self.assertIn("Do not navigate to the NotebookLM home/list page", prompt)
        self.assertIn("Do not navigate to find a notebook", prompt)
        self.assertIn("Do not start a new generation in observation mode", prompt)
        self.assertNotIn("download", prompt.lower())
        self.assertIn("Do not poll for completion in observation mode", prompt)
        self.assertIn("Stop immediately after the first snapshot", prompt)

    def test_mcp_agent_outline_first_skips_slide_deck_generation(self) -> None:
        prompt = _build_user_prompt(Path("/tmp/source.txt"), Path("/tmp/out"), outline_first=True)

        self.assertIn("generating a slide outline in chat", prompt)
        self.assertIn("Do not click Slide Deck", prompt)
        self.assertIn("Do not click Generate", prompt)
        self.assertIn("Return the generated outline content", prompt)

    def test_mcp_agent_fresh_notebook_prompt_avoids_failed_notebook(self) -> None:
        prompt = _build_user_prompt(Path("/tmp/source.txt"), Path("/tmp/out"), fresh_notebook=True)

        self.assertIn("create a fresh new notebook", prompt)
        self.assertIn("Do not reuse the current notebook", prompt)

    def test_snapshot_slide_deck_signal_marks_browser_workflow(self) -> None:
        self.assertTrue(_snapshot_shows_slide_deck_workflow("button: 正在生成簡報... 根據1 個來源"))
        self.assertTrue(_snapshot_shows_slide_deck_workflow("button: Start slideshow"))
        self.assertFalse(_snapshot_shows_slide_deck_workflow("button: 簡報"))
        self.assertFalse(_snapshot_shows_slide_deck_workflow("NotebookLM home page"))

    def test_assistant_blocked_report_overrides_snapshot_guess(self) -> None:
        self.assertTrue(_assistant_reported_blocked("blocked\n\nObserved state: 0 sources"))
        self.assertTrue(_assistant_reported_blocked("status=blocked\nmessage=No generation"))
        self.assertFalse(_assistant_reported_blocked("generation_started"))


class CliTests(unittest.TestCase):
    def test_mcp_agent_help_lists_model_and_cdp(self) -> None:
        proc = subprocess.run(
            [sys.executable, "scripts/notebooklm_ppt_mcp_agent.py", "--help"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("--model", proc.stdout)
        self.assertIn("--cdp-url", proc.stdout)
        self.assertIn("--max-wait-minutes", proc.stdout)
        self.assertIn("--fresh-notebook", proc.stdout)
        self.assertIn("--outline-first", proc.stdout)
        self.assertIn("--smoke-tools-only", proc.stdout)
        self.assertIn("--observe-existing-generation", proc.stdout)
        self.assertIn("Playwright MCP", proc.stdout)


if __name__ == "__main__":
    unittest.main()
