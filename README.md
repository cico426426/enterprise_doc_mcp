# EnterpriseDocMcp

Remote MCP server for searching parsed enterprise documents. The project ingests a PDF annual report and a PPTX economic presentation, extracts text/tables/selected visual content, chunks the records into ChromaDB, and exposes retrieval tools over MCP Streamable HTTP.

## Architecture

The project has one preprocessing core and two delivery surfaces:

```text
PDF/PPTX files
  -> skills/parse_documents
     parse text, tables, slide text, and optional vision summaries
  -> skills/chunk_and_index
     chunk records, embed text, persist vectors in Chroma
  -> mcp_server
     expose search, search_by_source, and list_documents over MCP Streamable HTTP

Claude Code Skills
  -> .claude/skills/parse-enterprise-documents
     parse-only inspection interface
  -> .claude/skills/index-enterprise-documents
     end-to-end parse/chunk/embed/index interface
```

Core modules:

- `skills/parse_documents/`: PDF/PPTX parsing, text cleanup, table markdown conversion, page/image rendering, optional vision summaries.
- `skills/chunk_and_index/`: chunking, local embedding, Chroma persistence, vector search, cross-encoder rerank.
- `scripts/ingest.py`: Task 1 ingest CLI; parses documents from `data/` and indexes them into Chroma.
- `mcp_server/`: FastMCP Streamable HTTP server with search tools and a health route.
- `.claude/skills/`: Task 2 Claude Code Skills that package the same preprocessing capability for agent-invoked parsing and indexing.
- `tests/eval_retriever.py`: Ragas context-metric evaluation for retriever quality.

Task 1 uses the core modules to serve a remote MCP knowledge base. Task 2 reuses the same modules through Claude Code Skills; it does not introduce a separate parser or indexer.

## How to run

Install dependencies:

```bash
uv sync --all-groups
```

Copy environment values:

```bash
cp .env.example .env
```

For local evaluation, set:

```env
OPENAI_API_KEY=...
RAGAS_JUDGE_MODEL=gpt-4o-mini
```

Ingest local documents:

```bash
uv run python scripts/ingest.py --reset --no-vision
```

Start the MCP server:

```bash
uv run python mcp_server/server.py
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected shape:

```json
{"status":"ok","has_data":true}
```

## MCP Usage

Streamable HTTP endpoint:

```text
http://127.0.0.1:8000/mcp
```

Public endpoint:

```text
https://enterprise-doc-mcp-yonghuei.zeabur.app/mcp
```

Exposed tools:

- `search(query: str, top_k: int = 5)`
- `search_by_source(filename: str, query: str, top_k: int = 5)`
- `list_documents()`

Cline remote MCP server example:

```json
{
  "mcpServers": {
    "enterprise-doc-mcp": {
      "url": "http://127.0.0.1:8000/mcp",
      "type": "streamableHttp",
      "disabled": false,
      "timeout": 120
    }
  }
}
```

Example queries:

```text
What documents are indexed?
```

```text
What does the World Bank presentation say about global growth?
```

```text
What downside risks does the World Bank presentation mention?
```

```text
Find Tesla total revenues for 2023, 2022, and 2021 in the revenues table.
```

```text
Find risks related to Tesla litigation.
```

```text
Find Tesla product liability risks.
```

These examples cover both indexed documents and show source-grounded retrieval across presentation slides, financial reports, and risk-related sections.

## Task 1: Remote MCP Server

Task 1 delivers the running MCP service. The service parses local enterprise documents, chunks and embeds the extracted records, stores them in Chroma, and exposes retrieval tools over Streamable HTTP.

Task 1 implementation entry points:

- `scripts/ingest.py`: local ingest workflow used by Docker/startup flows.
- `mcp_server/server.py`: FastMCP Streamable HTTP server.
- `mcp_server/_search.py`: retrieval adapter over the persisted Chroma index.

Use the commands in "How to run", "MCP Usage", and "Docker And Zeabur" to verify Task 1.

## Task 2: Claude Skills Packaging

Task 2 packages the same preprocessing capability behind Claude Code project Skills. These Skills are the supported interface for Claude-assisted preprocessing work:

- `.claude/skills/parse-enterprise-documents/SKILL.md`
- `.claude/skills/parse-enterprise-documents/scripts/parse.py`
- `.claude/skills/index-enterprise-documents/SKILL.md`
- `.claude/skills/index-enterprise-documents/scripts/ingest.py`

The reusable demo inputs are committed under `tests/fixtures/task2-input/` so reviewers can rerun the Skill examples without relying on local `.cache/` files.

Use `parse-enterprise-documents` when the user asks to parse or inspect PDF/PPTX content. Use `index-enterprise-documents` when the user asks to build, refresh, or validate a searchable index. The index Skill is the higher-level workflow: it already handles parsing, chunking, embedding, and Chroma persistence internally, so it should not call the parse Skill first unless the user explicitly asks for a separate parse-only inspection.

Safe boundary:

- For interview/demo evidence, prefer invoking the Skill command from `SKILL.md` directly instead of running exploratory shell commands first.
- Claude Code may check user-provided paths only when needed to resolve an ambiguous or failing input.
- Claude Code should execute Skill scripts with `uv run python ${CLAUDE_SKILL_DIR}/scripts/...` so project dependencies are available.
- For index requests, Claude Code should run only `index-enterprise-documents`; it should not run `parse-enterprise-documents` first unless the user explicitly asks to inspect parsed records.
- Both Skills accept `--data-dir`, `--source-dir`, and `--input-dir` for directory input; examples prefer `--data-dir` for indexing and `--source-dir` for parse-only inspection.
- Public demo and credential-free runs should use `--no-vision`.
- External vision credentials are optional and should only be used when intentionally configured.

Task 2 verification:

```bash
uv run python -m unittest -q tests/test_claude_skills.py
uv run python .claude/skills/index-enterprise-documents/scripts/ingest.py --help
rg -n 'uv run python|CLAUDE_SKILL_DIR|--data-dir|--source-dir|--input-dir|Do not run `parse-enterprise-documents` first' .claude/skills/*/SKILL.md
```

The index help should show `--data-dir`, `--source-dir`, and `--input-dir`. See `tests/skill_execution.log` for copied Skill invocation evidence and boundary checks.

Task 2 evidence files:

- `tests/fixtures/task2-input/`: committed PDF/PPTX inputs for rerunning the Skill examples.
- `tests/skill_execution.log`: copied command/output evidence for parse and index Skill runs.
- `tests/screenshots/parse-enterprise-documents-skills.png`: Claude Code using the parse Skill.
- `tests/screenshots/index-enterprise-documents-skills.png`: Claude Code using the index Skill.

## Task 3: NotebookLM PPT Browser Agent

Task 3 adds a browser agent that drives NotebookLM through the real web UI and asks NotebookLM to generate a Slide Deck about the project implementation workflow. The supported implementation is the LangChain `create_agent` path backed by Microsoft Playwright MCP browser tools; the old selector-only Playwright entry point was removed because it could stall in the operating system file picker.

Task 3 implementation entry points:

- `task3_notebooklm_agent/config.py`: NotebookLM prompt and Task 3 constants.
- `task3_notebooklm_agent/source_bundle.py`: deterministic source bundle generator for the NotebookLM upload.
- `task3_notebooklm_agent/mcp_agent.py`: LangChain + Playwright MCP browser agent.
- `scripts/notebooklm_ppt_mcp_agent.py`: CLI wrapper for the browser workflow.

The agent prepares a concise project source at `project-workflow-source.txt`, uploads it to a fresh NotebookLM notebook, selects Studio > Slide Deck, sets the output language to Traditional Chinese, pastes the custom prompt, clicks Generate exactly once, and stops after capturing browser evidence that generation started. It does not wait for export/download because NotebookLM Slide Deck generation can take several minutes and the browser workflow evidence is the hard gate.

Run the live workflow with an already-authenticated Chrome session exposed through CDP:

```bash
uv run --group task3 python scripts/notebooklm_ppt_mcp_agent.py \
  --cdp-url http://127.0.0.1:9222 \
  --output-dir task3-notebooklm \
  --model openai:gpt-5 \
  --recursion-limit 80 \
  --max-wait-minutes 5 \
  --fresh-notebook
```

The command writes raw local run output under `task3-notebooklm/`. That directory is intentionally ignored because browser snapshots can include account labels and local machine paths. A sanitized copy of the successful run is committed under `tests/artifacts/task3-notebooklm-run/`.

Task 3 verification:

```bash
uv run --group task3 python -m unittest -q tests/test_notebooklm_ppt_agent.py
rg -n 'NotebookLM|Slide Deck|generation_started|generation|screenshot|snapshot' tests/notebooklm_ppt_agent_execution.log
test -s tests/screenshots/notebooklm-ppt-generation-started.yml
test -s tests/artifacts/notebooklm-ppt-agent-result.json
test -s tests/artifacts/notebooklm-upload-manifest.json
```

Task 3 evidence files:

- `tests/notebooklm_ppt_agent_execution.log`: sanitized MCP browser agent run log.
- `tests/screenshots/notebooklm-ppt-generation-started.yml`: Playwright snapshot showing NotebookLM entered Slide Deck generation.
- `tests/artifacts/notebooklm-ppt-agent-result.json`: structured result with `generation_started` status.
- `tests/artifacts/notebooklm-upload-manifest.json`: source upload manifest.
- `tests/artifacts/task3-notebooklm-run/`: sanitized full browser run directory with prompt, source, log, console output, result JSON, manifest, and page snapshots.
- `tests/artifacts/EnterpriseDocMcp_Engineering_Blueprint.pptx`: manually downloaded supplemental NotebookLM PPTX artifact.

Key assumptions:

- NotebookLM requires an authenticated Google session, so the full external browser workflow is manual-assisted automation, not a headless CI-only test.
- NotebookLM UI text and Slide Deck beta behavior can change; the committed evidence records the successful browser workflow state used for Task 3.
- The agent must upload all selected sources before generation and must not retry Generate after a NotebookLM failure message.

## Verify

Unit tests:

```bash
uv run python -m unittest -q tests/test_text_table.py tests/test_render.py tests/test_vision.py tests/test_parse_documents.py tests/test_index_store.py tests/test_ingest.py tests/test_eval_retriever.py tests/test_mcp_server.py
```

Retriever evaluation:

```bash
uv run --group eval python tests/eval_retriever.py
```

Latest live Ragas retriever result:

```json
{
  "context_precision": 0.5528,
  "context_recall": 1.0,
  "ragas_context_score": 0.7764,
  "source_top1_rate": 1.0,
  "evaluated_queries": 6
}
```

MVP hard gate:

- `context_recall >= 0.9`
- `source_top1_rate >= 0.8`
- `context_precision` is reported as a diagnostic metric and future rerank/top-k tuning target.

MCP Docker smoke:

```bash
docker build -t enterprise-doc-mcp .
docker run -d --name enterprise-doc-mcp \
  -p 8000:8000 \
  -v "$PWD/chroma:/app/chroma" \
  -e CHROMA_PATH=/app/chroma \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  enterprise-doc-mcp
curl http://127.0.0.1:8000/health
```

Container MCP client smoke verified. See `tests/test_output.log` for copied command outputs and verification notes:

- Tools: `search`, `search_by_source`, `list_documents`
- `list_documents` returned 2 indexed sources:
  - `GEP-June-2024-Presentation.pptx` with 13 chunks
  - `tsla-20231231-gen.pdf` with 284 chunks

## Docker And Zeabur

The image excludes eval-only Ragas dependencies from production installs:

```bash
uv sync --locked --no-install-project --no-dev --no-group eval --no-group task3
```

Task 3 browser-agent dependencies live in the `task3` dependency group, so Task 1 Docker/Zeabur deployments do not install LangChain or NotebookLM automation libraries.

`zbpack.json`:

```json
{
  "build_command": "uv run python scripts/ingest.py --skip-if-exists --no-vision",
  "start_command": "uv run python mcp_server/server.py"
}
```

Docker deployments start through `scripts/start_server.py`, which runs a startup ingest with `skip_if_exists=True` before launching the MCP server. This keeps a fresh Zeabur volume usable without manually running a one-off ingest command.

Suggested Zeabur settings:

```env
CHROMA_PATH=/app/chroma
EMBED_CACHE_DIR=/app/.cache/embeddings
HOST=0.0.0.0
PORT=8000
ENABLE_VISION=0
STARTUP_INGEST=1
```

Persistent volume:

```text
/app/chroma
```

Public URL:

```text
https://enterprise-doc-mcp-yonghuei.zeabur.app/
```

After deployment, verify:

```bash
curl https://enterprise-doc-mcp-yonghuei.zeabur.app/health
```

## Assumptions and limits

- The local demo indexes `data/tsla-20231231-gen.pdf` and `data/GEP-June-2024-Presentation.pptx`.
- Chroma data is persisted outside Git and should be stored in a mounted volume for deployment.
- PPTX vision analyzes embedded picture objects; it does not render the full slide canvas. Slide text retrieval works reliably, while full chart understanding is a future improvement.
- Ragas is an eval-only dependency group and is intentionally excluded from the production Docker image.
- First Docker builds are slow because production still installs local retrieval dependencies such as `sentence-transformers`, `torch`, `chromadb`, and `onnxruntime`.

## Task requirements mapping

- Unstructured data pipeline: `scripts/ingest.py` parses PDF/PPTX files from `data/`, cleans/chunks records, embeds them, and stores them in Chroma.
- Remote MCP server: `mcp_server/server.py` exposes Streamable HTTP tools that standard MCP clients can call.
- Verifiable outputs: `tests/test_output.log` records unit tests, Ragas eval, MCP client smoke, Docker health, and Docker MCP client results.
- AI-only workflow: implementation was completed through an agent workflow with phase records in `plan/runtime_control.json` and `plan/progress.md`; Task 3 uses a browser agent to drive NotebookLM through Playwright MCP.
- Git evidence: history is organized as phase-level commits plus focused evaluation/deployment commits.
- Deploy online: Docker and Zeabur config are included; public URL is `https://enterprise-doc-mcp-yonghuei.zeabur.app/`.
- Documentation: this README includes how to run/verify Task 1, Task 2, and Task 3, plus assumptions and AI workflow notes.
- No confidential material: source documents are public/sample materials, and secrets are excluded through `.gitignore`.

## AI Workflow

Implementation followed a phase contract tracked in `plan/runtime_control.json` and `plan/progress.md`. Each completed phase records validation commands and evidence before commit. Git history is kept phase-oriented so reviewers can inspect the project progression without noisy fixup commits.
