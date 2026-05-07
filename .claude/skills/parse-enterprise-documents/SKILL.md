---
name: parse-enterprise-documents
description: Parse enterprise PDF and PPTX files into normalized records with cleaned text, table markdown, document metadata, and optional vision summaries. Use for parse-only inspection, debugging, or record review. Do not use this before indexing; use index-enterprise-documents directly when the user asks to build or refresh a searchable index.
allowed-tools: Bash(uv run python *)
---

# Parse Enterprise Documents

Use this Skill to extract normalized records from supported enterprise documents for inspection or debugging. For searchable index creation, use `index-enterprise-documents` directly instead of running this Skill first.

## Inputs

- `--file`: Local `.pdf` or `.pptx` path.
- `--type`: `pdf` or `pptx`; required with `--file`.
- `--source-dir`: Directory containing `.pdf` and `.pptx` files for batch parsing.
- `--data-dir`: Compatibility alias for `--source-dir`.
- `--input-dir`: Compatibility alias for `--source-dir`.
- `--no-vision`: Use for public demo and credential-free runs (recommended default).
- `--vision-provider`: Optional provider override when external vision credentials are intentionally configured.

## Outputs

The script writes a JSON array to stdout. Each record includes:

- `source_file`: Original document path
- `doc_type`: `pdf` or `pptx`
- `kind`: `text`, `table`, `slide_text`, or `slide_visuals`
- `text`: Cleaned and normalized text content
- Location metadata: `page_start` / `page_end` or `slide_number`
- Flags: `has_table`, `has_visuals`, `vision_analyzed`

## Safe Execution Boundary

- **Format restriction**: Only accepts PDF and PPTX files. Rejects unsupported formats.
- **Read-only operation**: Does not modify source documents.
- **Credential isolation**: Vision analysis is optional. Use `--no-vision` for public demos.
- **Output control**: Writes to stdout only. No file system modifications.

## Commands

Parse a single PPTX file:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/parse.py --file data/GEP-June-2024-Presentation.pptx --type pptx --no-vision
```

Parse a single PDF file:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/parse.py --file data/tsla-20231231-gen.pdf --type pdf --no-vision
```

Batch parse a directory:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/parse.py --source-dir tests/fixtures/task2-input --no-vision
```

Get help:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/parse.py --help
```

## Usage Notes

- For inspection and research, invoke this Skill to see parsed structure.
- Do not use this before indexing; use `index-enterprise-documents` directly for searchable index creation.
- For building a searchable index, use `index-enterprise-documents` instead; it handles parsing internally and should be the only Skill invoked for indexing requests.
- Directory parameter guidance: prefer `--source-dir`; `--data-dir` and `--input-dir` are accepted aliases.
- Summarize record counts unless full JSON output is explicitly requested.
