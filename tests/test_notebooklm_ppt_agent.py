from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from task3_notebooklm_agent.auth import session_path
from task3_notebooklm_agent.config import SLIDE_DECK_PROMPT
from task3_notebooklm_agent.source_bundle import build_source_bundle


ROOT = Path(__file__).resolve().parents[1]


class SourceBundleTests(unittest.TestCase):
    def test_build_source_bundle_uses_public_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = build_source_bundle(ROOT, Path(tmp))

            self.assertTrue(result.source_path.exists())
            self.assertTrue(result.prompt_path.exists())
            body = result.source_path.read_text(encoding="utf-8")

        self.assertIn("EnterpriseDocMcp Project Workflow Source", body)
        self.assertIn("Source: plan/task.txt", body)
        self.assertIn("Source: README.md", body)
        self.assertIn("Slide Deck", body)
        self.assertIn("Do not mention interviewers", body)
        self.assertIn("OPENAI_API_KEY=[redacted]", body)
        self.assertNotIn("OPENAI_API_KEY=...", body)
        self.assertNotIn("ANTHROPIC_API_KEY=...", body)

    def test_prompt_mentions_required_deck_content(self) -> None:
        self.assertIn("Task 1", SLIDE_DECK_PROMPT)
        self.assertIn("Task 2", SLIDE_DECK_PROMPT)
        self.assertIn("Task 3", SLIDE_DECK_PROMPT)
        self.assertIn("Claude Skills", SLIDE_DECK_PROMPT)


class AuthPathTests(unittest.TestCase):
    def test_session_path_stays_under_output_dir(self) -> None:
        self.assertEqual(session_path(Path(".cache/task3-notebooklm")), Path(".cache/task3-notebooklm/session.json"))


class CliTests(unittest.TestCase):
    def test_help_lists_prepare_and_login(self) -> None:
        proc = subprocess.run(
            [sys.executable, "scripts/notebooklm_ppt_agent.py", "--help"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("--prepare-only", proc.stdout)
        self.assertIn("login", proc.stdout)

    def test_prepare_only_writes_result_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    "scripts/notebooklm_ppt_agent.py",
                    "--prepare-only",
                    "--output-dir",
                    tmp,
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )
            payload = json.loads(proc.stdout)
            source_path = Path(payload["source_path"])
            result_path = Path(payload["result_path"])

            self.assertEqual(payload["status"], "prepared")
            self.assertTrue(source_path.exists())
            self.assertTrue(result_path.exists())


if __name__ == "__main__":
    unittest.main()
