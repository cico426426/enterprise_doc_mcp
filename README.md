# EnterpriseDocMcp

Remote MCP server for searching parsed enterprise documents. The project ingests a PDF annual report and a PPTX economic presentation, extracts text/tables/selected visual content, chunks the records into ChromaDB, and exposes retrieval tools over MCP Streamable HTTP.

## Architecture

- `skills/parse_documents/`: PDF/PPTX parsing, text cleanup, table markdown conversion, page/image rendering, optional vision summaries.
- `skills/chunk_and_index/`: chunking, local embedding, Chroma persistence, vector search, cross-encoder rerank.
- `scripts/ingest.py`: parse documents from `data/` and index them into Chroma.
- `mcp_server/`: FastMCP Streamable HTTP server with search tools and a health route.
- `tests/eval_retriever.py`: Ragas context-metric evaluation for retriever quality.

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
What was Tesla's 2023 total revenue?
```

```text
Find risks related to Tesla litigation.
```

```text
Find Tesla product liability risks.
```

These examples cover both indexed documents and show source-grounded retrieval across presentation slides, financial reports, and risk-related sections.

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
uv sync --locked --no-install-project --no-dev --no-group eval
```

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
- AI-only workflow: implementation was completed through an agent workflow with phase records in `plan/runtime_control.json` and `plan/progress.md`.
- Git evidence: history is organized as phase-level commits plus focused evaluation/deployment commits.
- Deploy online: Docker and Zeabur config are included; public URL is `https://enterprise-doc-mcp-yonghuei.zeabur.app/`.
- Documentation: this README includes how to run/verify, assumptions, and AI workflow notes.
- No confidential material: source documents are public/sample materials, and secrets are excluded through `.gitignore`.

## AI Workflow

Implementation followed a phase contract tracked in `plan/runtime_control.json` and `plan/progress.md`. Each completed phase records validation commands and evidence before commit. Git history is kept phase-oriented so reviewers can inspect the project progression without noisy fixup commits.
