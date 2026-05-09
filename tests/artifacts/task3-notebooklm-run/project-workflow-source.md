# EnterpriseDocMcp Implementation Workflow

This is a curated source for a NotebookLM Slide Deck. It contains only presentation material, not prompts, raw logs, runtime JSON, credentials, browser state, or implementation transcripts.

## Executive Summary

EnterpriseDocMcp is an engineering project that converts enterprise documents into an AI-ready knowledge workflow. The work is currently tracked at phase-17, with 17 completed phases recorded in runtime control. The system parses documents, indexes them for retrieval, exposes search through a remote MCP server, packages preprocessing workflows as Claude Skills, and uses a browser agent to generate NotebookLM presentation evidence. The project emphasizes traceable phase execution, repeatable validation, and disciplined human-AI collaboration.

## Task 1: Remote MCP Server

Task 1 delivers the core document intelligence service. It includes parsing modules for text, tables, rendered pages, vision-assisted analysis, PDF files, and PowerPoint files. Parsed records are chunked, embedded, stored in Chroma, and retrieved through search tools. The MCP server exposes document search, source-specific search, and document listing capabilities so external AI tools can query the indexed enterprise knowledge base. Deployment is packaged with Docker and validated with server health checks and MCP client smoke tests.

Key points for the deck:
- Converts unstructured enterprise files into searchable chunks.
- Uses parsing, chunking, embeddings, vector storage, reranking, and retrieval evaluation.
- Exposes capabilities through a FastMCP server.
- Supports local and deployment validation through tests, health checks, and client calls.

## Task 2: Claude Skills Packaging

Task 2 turns the preprocessing workflow into reusable Claude Skills. The parse Skill handles enterprise document parsing with clear input and output expectations. The index Skill wraps ingestion and indexing commands with directory aliases and safe execution boundaries. The Skills include direct command examples, script references, fixture-based validation, and rules that prevent unsafe or unnecessary execution.

Key points for the deck:
- Packages parsing and indexing as reusable AI-callable workflows.
- Documents safe boundaries, commands, inputs, and outputs.
- Uses fixture inputs and unit tests as verification evidence.
- Keeps Task 2 distinct from the remote MCP server in Task 1.

## Task 3: NotebookLM Browser Agent

Task 3 automates NotebookLM through a real browser workflow. The final design uses LangChain create_agent with Microsoft Playwright MCP browser tools connected to an already-authenticated Chrome session through CDP. The browser agent uploads a curated project source, optionally uses NotebookLM chat to produce an outline first, then triggers NotebookLM Slide Deck generation. Success is accepted when the browser workflow reaches source upload plus Slide Deck generation evidence in logs, screenshots, snapshots, and result JSON.

Key points for the deck:
- Uses a real NotebookLM UI workflow rather than fabricating slides locally.
- Uses Playwright MCP tools instead of brittle selector-only browser code.
- Avoids repeated generation attempts because NotebookLM Slide Deck is a beta feature.
- Records output logs, upload manifests, screenshots, snapshots, and result JSON.

## Phase-Based Engineering Workflow

The project is managed through explicit phase files and runtime control metadata. Each phase defines scoped work, required paths, validation commands, status, notes, and commit gates. The workflow requires validation before completion and prohibits automatic commits. Progress is recorded in a human-readable progress log so the implementation history remains auditable.

Key points for the deck:
- Each phase has a bounded implementation scope.
- Validation commands are part of the contract, not an afterthought.
- Blocked states are recorded when external systems fail or evidence is incomplete.
- User approval is required before commits.

## Human-AI Collaboration

The implementation improved through direct human feedback. The user identified that the first browser approach stalled in the operating system file manager, that committing before evidence would be wrong, and that repeated Slide Deck generation wastes limited NotebookLM attempts. These corrections shifted the design toward a stricter MCP browser agent, cleaner source generation, single-generation rules, bounded waiting, and an outline-first safety mode.

Key points for the deck:
- Human review caught false completion and incorrect automation assumptions.
- Browser automation was simplified to one official MCP path.
- Source content was curated to avoid prompts, logs, and irrelevant screenshots.
- Evidence gates prevented incomplete Task 3 completion.

## Validation Evidence

Validation combines automated checks and external workflow evidence. Automated checks include unit tests, py_compile, CLI help checks, JSON validation, Docker smoke tests, MCP client checks, and Skill execution tests. External NotebookLM evidence requires a run log, upload manifest, result JSON, and screenshot or snapshot evidence that source upload and Slide Deck generation were actually driven in the browser.

Key points for the deck:
- Dockerfile and zbpack.json added. Validation command cat zbpack.json passed; JSON parsed successfully; ingest --help and py_compile for ingest/server passed. ragas moved to the eval dependency group, and Docker production sync excludes eval-only dependencies with --no-group eval to reduce build time. docker build -t enterprise-doc-mcp . completed; docker run with mounted chroma returned /health status ok with has_data=true; MCP streamable HTTP client listed tools and called list_documents successfully. current_phase advanced to phase-10.
- README.md and tests/test_output.log added; README validation command passes and includes run, verify, assumptions, AI workflow, Docker, MCP, and Zeabur instructions. Public Zeabur URL is available at https://enterprise-doc-mcp-yonghuei.zeabur.app/. Added scripts/start_server.py and changed Docker CMD so startup ingest runs before server start. py_compile and ingest/MCP unit tests pass. Redeployed health check returned {"status":"ok","has_data":true}; phase-10 completed.
- Refactored to match Skills script pattern: tests verify structure (scripts/, ${CLAUDE_SKILL_DIR}, allowed-tools), execution commands follow SKILL.md examples through uv run python, and log renamed to skill_execution.log. Added common directory aliases (--data-dir, --source-dir, --input-dir) across parse and index CLIs to prevent parameter mismatch.
- README Task 2 section clarified the Claude Skills packaging boundary, script-based Skill execution evidence, uv run python dependency environment, committed fixture inputs, and stricter guidance to avoid running parse before index requests. Validation passed: README rg check, runtime_control JSON parse, and uv run python -m unittest -q tests/test_claude_skills.py.