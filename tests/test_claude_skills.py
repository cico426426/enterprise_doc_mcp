import json
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.ingest import _discover_files
from skills.parse_documents.parse import discover_documents, parse_document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = PROJECT_ROOT / ".claude" / "skills"


def _load_skill(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0] != "":
        raise AssertionError(f"Invalid frontmatter delimiters: {path}")

    metadata: dict[str, str] = {}
    for raw_line in parts[1].strip().splitlines():
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, parts[2]


def _load_python_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClaudeSkillStructureTests(TestCase):
    def test_project_skills_have_valid_frontmatter(self) -> None:
        expected_names = {
            "parse-enterprise-documents",
            "index-enterprise-documents",
        }

        paths = sorted(SKILL_DIR.glob("*/SKILL.md"))
        names = set()
        for path in paths:
            metadata, _ = _load_skill(path)
            names.add(metadata["name"])
            self.assertRegex(metadata["name"], r"^[a-z0-9-]{1,64}$")
            self.assertGreater(len(metadata["description"]), 80)
            # Check for allowed-tools (official pattern for pre-authorization)
            self.assertIn("allowed-tools", metadata)

        self.assertTrue(expected_names.issubset(names))

    def test_skills_document_inputs_outputs_boundaries_and_commands(self) -> None:
        required_sections = [
            "## Inputs",
            "## Outputs",
            "## Safe Execution Boundary",
            "## Commands",
        ]
        required_terms = [
            "--no-vision",
            "${CLAUDE_SKILL_DIR}",  # Official variable for skill directory
        ]

        for path in sorted(SKILL_DIR.glob("*/SKILL.md")):
            _, body = _load_skill(path)
            for section in required_sections:
                self.assertIn(section, body, path)
            for term in required_terms:
                self.assertIn(term, body, path)

    def test_skills_have_scripts_directory(self) -> None:
        for skill_dir in sorted(SKILL_DIR.glob("*")):
            if not skill_dir.is_dir():
                continue
            scripts_dir = skill_dir / "scripts"
            self.assertTrue(scripts_dir.exists(), f"Missing scripts/: {scripts_dir}")
            self.assertTrue(scripts_dir.is_dir(), f"Not a directory: {scripts_dir}")

            # Check for expected script
            if skill_dir.name == "parse-enterprise-documents":
                self.assertTrue((scripts_dir / "parse.py").exists())
            elif skill_dir.name == "index-enterprise-documents":
                self.assertTrue((scripts_dir / "ingest.py").exists())

    def test_skill_md_uses_official_patterns(self) -> None:
        """Verify Skills follow official Claude Code patterns"""
        for path in sorted(SKILL_DIR.glob("*/SKILL.md")):
            _, body = _load_skill(path)

            # Should use ${CLAUDE_SKILL_DIR} for script references
            self.assertIn("${CLAUDE_SKILL_DIR}/scripts/", body)

            # Should run inside the project dependency environment.
            self.assertIn("uv run python", body)

            # Should not reference old wrapper pattern
            self.assertNotIn("run.sh", body)


class SkillContentTests(TestCase):
    def test_parse_skill_documents_format_and_source_boundaries(self) -> None:
        _, body = _load_skill(SKILL_DIR / "parse-enterprise-documents" / "SKILL.md")

        # Format boundaries
        self.assertIn(".pdf", body)
        self.assertIn(".pptx", body)

        # Usage guidance
        self.assertIn("--source-dir", body)
        self.assertIn("index-enterprise-documents", body)

        # Safety boundaries
        self.assertIn("Format restriction", body)
        self.assertIn("Read-only", body)
        self.assertIn("Credential isolation", body)

    def test_index_skill_documents_write_and_reset_boundaries(self) -> None:
        _, body = _load_skill(SKILL_DIR / "index-enterprise-documents" / "SKILL.md")

        # Configuration
        self.assertIn("CHROMA_PATH", body)
        self.assertIn("--skip-if-exists", body)
        self.assertIn("--reset", body)

        # Safety guidance
        self.assertIn("Reset control", body)
        self.assertIn(".cache/task2-skill-chroma", body)

        # Write boundaries
        self.assertIn("Write isolation", body)
        self.assertIn("Do not run `parse-enterprise-documents` first", body)
        self.assertIn("--source-dir", body)

    def test_parse_skill_defers_indexing_requests_to_index_skill(self) -> None:
        _, body = _load_skill(SKILL_DIR / "parse-enterprise-documents" / "SKILL.md")

        self.assertIn("Do not use this before indexing", body)
        self.assertIn("index-enterprise-documents", body)


class SkillRuntimeValidationTests(TestCase):
    def test_task2_phases_reference_correct_commands(self) -> None:
        runtime_path = PROJECT_ROOT / "plan" / "runtime_control.json"
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        phases = {phase["id"]: phase for phase in runtime["phases"]}

        # Phase 13 should reference Skill scripts through the project uv environment.
        phase13_commands = "\n".join(
            phases["phase-13"]["implementation_check"]["validation_commands"]
        )
        self.assertIn("uv run python", phase13_commands)
        self.assertIn("scripts/parse.py", phase13_commands)
        self.assertIn("scripts/ingest.py", phase13_commands)

    def test_index_script_accepts_source_dir_alias(self) -> None:
        ingest_path = SKILL_DIR / "index-enterprise-documents" / "scripts" / "ingest.py"
        module = _load_python_module(ingest_path)

        args = module._build_parser().parse_args(
            ["--source-dir", "tests/fixtures/task2-input", "--reset", "--no-vision"]
        )

        self.assertEqual(args.data_dir, "tests/fixtures/task2-input")
        self.assertTrue(args.reset)
        self.assertTrue(args.no_vision)

    def test_index_script_accepts_input_dir_alias(self) -> None:
        ingest_path = SKILL_DIR / "index-enterprise-documents" / "scripts" / "ingest.py"
        module = _load_python_module(ingest_path)

        args = module._build_parser().parse_args(
            ["--input-dir", "tests/fixtures/task2-input", "--reset", "--no-vision"]
        )

        self.assertEqual(args.data_dir, "tests/fixtures/task2-input")
        self.assertTrue(args.reset)
        self.assertTrue(args.no_vision)

    def test_parse_script_accepts_common_directory_aliases(self) -> None:
        parse_path = SKILL_DIR / "parse-enterprise-documents" / "scripts" / "parse.py"
        module = _load_python_module(parse_path)

        for flag in ("--source-dir", "--data-dir", "--input-dir"):
            args = module._build_parser().parse_args(
                [flag, "tests/fixtures/task2-input", "--no-vision"]
            )
            self.assertEqual(args.source_dir, "tests/fixtures/task2-input")
            self.assertTrue(args.no_vision)


class SkillBoundaryBehaviorTests(TestCase):
    """Test that Skills enforce proper file-level boundaries"""

    def test_parse_document_rejects_unsupported_type(self) -> None:
        with self.assertRaises(ValueError):
            parse_document("data/tsla-20231231-gen.pdf", "docx")  # type: ignore[arg-type]

    def test_parse_discovery_only_finds_pdf_and_pptx(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            pdf = base / "a.pdf"
            pptx = base / "b.pptx"
            ignored = base / "c.txt"
            pdf.write_text("pdf", encoding="utf-8")
            pptx.write_text("pptx", encoding="utf-8")
            ignored.write_text("ignored", encoding="utf-8")

            out = discover_documents(base)

        self.assertEqual([p.name for p in out], ["a.pdf", "b.pptx"])

    def test_ingest_discovers_only_pdf_and_pptx(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            pdf = base / "a.pdf"
            pptx = base / "b.pptx"
            ignored = base / "c.txt"
            pdf.write_text("pdf", encoding="utf-8")
            pptx.write_text("pptx", encoding="utf-8")
            ignored.write_text("ignored", encoding="utf-8")

            out = _discover_files(base)

        self.assertEqual([p.name for p in out], ["a.pdf", "b.pptx"])
