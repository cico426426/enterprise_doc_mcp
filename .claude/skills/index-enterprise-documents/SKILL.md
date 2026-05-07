---
name: index-enterprise-documents
description: Build or refresh the searchable EnterpriseDocMcp Chroma index directly from local PDF/PPTX source files. Use this when the user asks to create an index, refresh an index, ingest documents, validate searchable retrieval data, or index a directory such as tests/fixtures/task2-input. Do not run the parse skill first for indexing requests.
allowed-tools: Bash(uv run python *)
---

# Index Enterprise Documents

Use this Skill to turn local PDF/PPTX source files into a persistent Chroma index for retrieval and MCP serving. For indexing requests, run this Skill directly; it already performs parsing, chunking, embedding, and persistence.

## Inputs

- `--data-dir`: Directory containing `.pdf` and `.pptx` files. Defaults to `data`.
- `--source-dir`: Compatibility alias for `--data-dir`. Prefer `--data-dir` in examples.
- `--input-dir`: Compatibility alias for `--data-dir`.
- `--reset`: Rebuild the Chroma collection from scratch.
- `--skip-if-exists`: Keep existing Chroma index and avoid duplicate work.
- `--no-vision`: Use for public demo and credential-free runs (recommended default).
- `CHROMA_PATH`: Environment variable for Chroma persistence directory. Defaults to `chroma/`.

## Outputs

The script prints a summary dictionary with:

- `processed_files`: Number of successfully processed documents
- `failed_files`: Number of documents that failed processing
- `chunk_count`: Total number of indexed chunks
- `skipped`: Whether existing index was preserved

Indexed chunks are persisted in the configured Chroma path and can be queried by the MCP server.

## Safe Execution Boundary

- **Format restriction**: Only processes PDF and PPTX files via the parser.
- **Write isolation**: Only writes to the configured `CHROMA_PATH`. Does not modify source files.
- **Credential isolation**: Vision analysis is optional. Use `--no-vision` for public demos.
- **Reset control**: Use `--reset` only when rebuilding is explicitly intended.

## Commands

Index `tests/fixtures/task2-input` without image/vision analysis:

```bash
CHROMA_PATH=.cache/task2-skill-chroma uv run python ${CLAUDE_SKILL_DIR}/scripts/ingest.py --data-dir tests/fixtures/task2-input --reset --no-vision
```

Build or refresh the default index:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/ingest.py --reset --no-vision
```

Build deployment-safe index (preserves existing):

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/ingest.py --skip-if-exists --no-vision
```

Build a temporary verification index:

```bash
CHROMA_PATH=.cache/task2-skill-chroma uv run python ${CLAUDE_SKILL_DIR}/scripts/ingest.py --data-dir tests/fixtures/task2-input --reset --no-vision
```

Get help:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/ingest.py --help
```

## Usage Notes

- This Skill handles parsing, chunking, embedding, and persistence end-to-end.
- Do not run `parse-enterprise-documents` first for indexing requests unless the user explicitly asks to inspect parsed records.
- For temporary verification, set `CHROMA_PATH=.cache/task2-skill-chroma`.
- Do not use the default `chroma/` path for temporary tests.
- Directory parameter guidance: prefer `--data-dir`; `--source-dir` and `--input-dir` are accepted aliases.
