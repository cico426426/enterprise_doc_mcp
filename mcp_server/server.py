import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

from mcp_server._search import run_list_documents, run_search, sources_json
from skills.chunk_and_index._store import has_data


mcp = FastMCP(
    name="enterprise-doc-mcp",
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000")),
    json_response=True,
    stateless_http=True,
)


@mcp.tool()
def search(query: str, top_k: int = 5) -> dict:
    """Search all indexed enterprise documents."""
    return run_search(query=query, top_k=top_k)


@mcp.tool()
def search_by_source(filename: str, query: str, top_k: int = 5) -> dict:
    """Search indexed chunks from one source filename."""
    return run_search(query=query, top_k=top_k, filename=filename)


@mcp.tool()
def list_documents() -> dict:
    """List indexed source documents and chunk counts."""
    return run_list_documents()


@mcp.resource("docs://sources")
def sources_resource() -> str:
    """Return indexed source documents as JSON."""
    return sources_json()


@mcp.custom_route("/health", methods=["GET"])
async def health(request) -> JSONResponse:
    return JSONResponse({"status": "ok", "has_data": has_data()})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
