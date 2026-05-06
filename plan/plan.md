# enterprise-doc-mcp — Execution Plan v5

> 目標：模組清晰、function signature 明確、讓 Codex 產出穩定可預期的 code。
> 原則：每個檔案的職責、輸入、輸出、邊界條件都完整定義，Codex 不需要猜測。

---

## 核心技術決策

| 項目 | 選擇 | 原因 |
|------|------|------|
| PDF 提取 | `pymupdf`（全文提取，不按頁切） | 解決跨頁問題 |
| PPTX 提取 | `python-pptx` | 輕量，不需要 LibreOffice |
| Chunking | LlamaIndex `SentenceSplitter` | 已經寫好，按 sentence boundary 切，不在句中截斷 |
| Parent-Child Chunk | **不用** | Tesla 10-K 是線性文件，512 token chunk 已夠，加了複雜度高收益低 |
| Embedding | `sentence-transformers` (`BAAI/bge-small-en-v1.5`) | 本地跑，免費，384 維，max 512 tokens |
| Vector Store | **ChromaDB**（本地 persistent） | 常見、簡單、有完整 metadata filter |
| Rerank | **加**，`cross-encoder/ms-marco-MiniLM-L-6-v2` | 財報查詢字面匹配重要，rerank 修正 pure vector search 排名錯誤 |
| Vision | Gemini Flash（免費方案） | 分析 PDF 圖表頁、PPTX 內嵌圖片 |
| MCP Framework | `FastMCP` | 官方支援 HTTP transport |
| Deploy | **Zeabur**（$5 方案 + persistent volume） | 不需要 ping 防 sleep，volume 持久化 ChromaDB |
| Ingest 觸發 | Zeabur one-off command（`zbpack.json`） | 部署時自動跑，不需要手動觸發 |

---

## Chunking 設計

用 LlamaIndex `SentenceSplitter`，全文提取後切：

```python
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(
    chunk_size=512,     # tokens，對齊 bge-small max 512 token limit
    chunk_overlap=64,   # 12.5% overlap，解決跨頁句子截斷
)
nodes = splitter.get_nodes_from_documents([doc])
```

優點：按 sentence boundary 切，不會在句子中間截斷，比自實作 sliding window 更穩定。

**不切 chunk 的情況：**
- PPTX slide → slide 天然是獨立單元，不切
- 表格 record → 結構化內容，不切，獨立存一個 chunk

**圖片處理：**
- 不切 chunk，vision 分析結果附加在所在頁/slide 的 chunk text 末尾
- 格式固定：
  ```
  [Visual Content]
  Summary: ...
  Charts: ...
  Text: ...
  ```
- 這樣語意搜尋「revenue chart」時能命中，上下文也保留

**表格處理：**
- 轉成 Markdown 後獨立成一個 chunk（不跟正文混）
- 原因：表格的語意是結構化的，混進正文會污染 embedding

---

## 檔案結構

```
enterprise-doc-mcp/
│
├── skills/
│   ├── parse_documents/
│   │   ├── SKILL.md
│   │   ├── __init__.py
│   │   ├── parse.py          ← 對外唯一入口，只做 dispatch
│   │   ├── _text.py          ← 純文字清理，不知道 PDF/PPTX 的存在
│   │   ├── _table.py         ← table → markdown，不知道 PDF/PPTX 的存在
│   │   ├── _render.py        ← 文件頁面 → bytes，不呼叫 Vision API
│   │   ├── _vision.py        ← bytes → dict，不碰檔案系統
│   │   ├── _pdf.py           ← PDF 解析，呼叫上面的模組
│   │   └── _pptx.py          ← PPTX 解析，呼叫上面的模組
│   │
│   └── chunk_and_index/
│       ├── SKILL.md
│       ├── __init__.py
│       ├── _embed.py         ← sentence-transformers 封裝
│       ├── _rerank.py        ← CrossEncoder rerank 封裝
│       ├── _store.py         ← ChromaDB 讀寫
│       └── index.py          ← orchestration：records → chunks → embed → store
│
├── mcp_server/
│   ├── __init__.py
│   ├── server.py             ← FastMCP，定義 tools 和 resource
│   └── _search.py            ← query → search → format
│
├── scripts/
│   └── ingest.py             ← CLI：parse + index，結果寫進 chroma/
│
├── tests/
│   ├── test_client_http.py
│   ├── eval_retriever.py     ← retriever 評估腳本
│   └── test_output.log
│
├── data/
│   ├── tsla-20231231-gen.pdf
│   └── GEP-June-2024-Presentation.pptx
│
├── zbpack.json               ← Zeabur 部署設定
├── .env.example
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Metadata Schema（ChromaDB）

ChromaDB metadata 只支援 `str | int | float | bool`，不支援 nested dict。

```python
# PDF chunk 的 metadata
{
    "source_file":      str,    # "tsla-20231231-gen.pdf"
    "doc_type":         str,    # "pdf"
    "page_start":       int,    # 從 1 開始
    "page_end":         int,    # 跨頁 chunk 的結束頁（單頁則 == page_start）
    "chunk_index":      int,    # 同一份文件的第幾個 chunk，從 0 開始
    "kind":             str,    # "text" | "table"
    "section":          str,    # 最近的標題，找不到為 ""
    "has_table":        bool,
    "has_visuals":      bool,
    "vision_analyzed":  bool,
}

# PPTX chunk 的 metadata
{
    "source_file":      str,    # "GEP-June-2024-Presentation.pptx"
    "doc_type":         str,    # "pptx"
    "slide_number":     int,    # 從 1 開始
    "chunk_index":      int,    # 固定為 0（slide 不切）
    "title":            str,    # slide 標題，找不到為 ""
    "kind":             str,    # "slide" | "table"
    "has_table":        bool,
    "has_visuals":      bool,
    "vision_analyzed":  bool,
}
```

---

## 模組規格（Codex 照這裡寫）

### `skills/parse_documents/_text.py`

**職責**：純文字清理。不 import fitz、pptx、任何 API。

```python
def clean(text: str) -> str:
    """
    移除不可見字元：\u00a0 → space、\x0b → \n、\u200b → ''
    連續空白壓縮成一個 space。
    連續換行超過 2 個壓縮成 2 個。
    回傳清理後的字串。空字串輸入回傳空字串。
    """

def merge_lines(lines: list[str]) -> list[str]:
    """
    把被意外斷行的句子合併。合併條件（滿足任一）：
    - 上一行以連字號結尾（去掉連字號合併）
    - 下一行以小寫字母開頭
    - 下一行以數字開頭且上一行不以句號結尾
    回傳合併後的 list[str]。輸入空 list 回傳空 list。
    """

def normalize_block(text: str) -> str:
    """
    clean() → 按換行切成 lines → merge_lines() → 重新 join。
    回傳處理後的字串。
    """

def iter_meaningful(text: str, min_len: int = 3) -> list[str]:
    """
    按換行切割，過濾掉：空行、長度 < min_len 的行、純空白行。
    回傳 list[str]。
    """
```

---

### `skills/parse_documents/_table.py`

**職責**：把二維資料轉成 Markdown table。不 import fitz、pptx、任何 API。

```python
def rows_to_markdown(rows: list[list[str]]) -> str:
    """
    輸入：二維 list，第一個 row 視為 header。
    輸出：Markdown table 字串。
    邊界條件：
    - 空 list → 回傳 ""
    - 只有一個 row → 回傳只有 header 和分隔線的 table
    - cell 內有 | 字元 → 轉義成 \|
    - cell 內有換行 → 轉成 space
    """
```

---

### `skills/parse_documents/_render.py`

**職責**：把文件頁面 render 成 bytes。不呼叫 Vision API，不做任何文字處理。

```python
def pdf_page_to_bytes(page: fitz.Page, scale: float = 2.0) -> bytes:
    """
    用 fitz 把單一 PDF 頁面 render 成 JPEG bytes。
    scale=2.0 → 約 1700x2200px，Vision API 足夠清晰。
    失敗時 raise RuntimeError，不回傳 None。
    """

def pptx_slide_to_bytes(slide_index: int, pptx_path: Path) -> bytes | None:
    """
    用 python-pptx 提取 slide 內嵌圖片的 bytes。
    策略：
    1. 遍歷 slide 的所有 shapes
    2. 找到第一個 MSO_SHAPE_TYPE.PICTURE 的 shape
    3. 回傳 shape.image.blob
    沒有圖片 → 回傳 None。
    不使用 LibreOffice，不 render 整張 slide。
    """
```

---

### `skills/parse_documents/_vision.py`

**職責**：把圖片 bytes 送給 Vision API，回傳結構化 dict。不碰檔案系統，不存 API key 到 globals。

```python
VisionResult = TypedDict("VisionResult", {
    "summary":      str,         # 整張圖的一句話描述
    "charts":       list[dict],  # [{"type": str, "title": str, "key_findings": str}]
    "text_content": str,         # 圖中所有可見文字
    "has_data":     bool,        # 是否包含數據圖表
})

def describe_image(
    img_bytes: bytes,
    provider: str | None = None,
) -> VisionResult | None:
    """
    provider 解析順序：參數 > VISION_PROVIDER env > "gemini"
    API key 每次 call 時從 env 讀，不存 globals：
      gemini    → GEMINI_API_KEY
      anthropic → ANTHROPIC_API_KEY
      openai    → OPENAI_API_KEY
    失敗（網路、API、JSON 解析）→ 回傳 None，不 raise。
    失敗時 log warning，key 在 log 裡 redact（只顯示前4後4字元）。
    img_bytes 為空 → 回傳 None。
    """
```

Prompt（固定，Codex 硬編進去）：
```
Analyze this image from a financial/business document.
Return ONLY valid JSON with this exact schema:
{
  "summary": "one sentence description",
  "charts": [{"type": "...", "title": "...", "key_findings": "..."}],
  "text_content": "all visible text",
  "has_data": true/false
}
No markdown, no explanation, only JSON.
```

---

### `skills/parse_documents/_pdf.py`

**職責**：PDF → list[Record]。跨頁問題在這裡解決。

```python
PDFRecord = TypedDict("PDFRecord", {
    "text":             str,
    "source_file":      str,
    "doc_type":         Literal["pdf"],
    "kind":             Literal["text", "table"],
    "page_start":       int,
    "page_end":         int,
    "section":          str,
    "has_table":        bool,
    "has_visuals":      bool,
    "vision_analyzed":  bool,
})

def parse_pdf(
    path: Path,
    enable_vision: bool = True,
    vision_provider: str | None = None,
) -> list[PDFRecord]:
    """
    步驟：
    1. 全文提取（不按頁切，解決跨頁問題）
       - 用 fitz 遍歷所有頁面
       - 每頁 text block → normalize_block()
       - 在每頁文字開頭插入頁碼標記 \f[PAGE:N]\f（N 從 1 開始）
       - 合併成 full_text，產生一個 kind="text" record
    2. 表格提取（按頁，獨立 record）
       - 每頁 page.find_tables()
       - rows_to_markdown() → 獨立 kind="table" record
       - page_start = page_end = 該頁頁碼，has_table = True
    3. Vision 分析（按頁，有圖才做）
       - page.get_images() 不為空 → pdf_page_to_bytes() → describe_image()
       - 結果附加到 full_text 末尾：
         \n\n[Visual Content - Page N]\nSummary: ...\nCharts: ...\nText: ...
       - kind="text" record 的 has_visuals = True，vision_analyzed = True
    4. 回傳 list[PDFRecord]

    注意：
    - 頁碼標記讓 index.py 切 chunk 後能還原 page_start/page_end
    - 空 PDF → 回傳 []
    - 開檔失敗 → raise ValueError(f"Cannot open PDF: {path}")
    """
```

---

### `skills/parse_documents/_pptx.py`

**職責**：PPTX → list[Record]。每張 slide 一個 Record。

```python
PPTXRecord = TypedDict("PPTXRecord", {
    "text":             str,
    "source_file":      str,
    "doc_type":         Literal["pptx"],
    "kind":             Literal["slide", "table"],
    "slide_number":     int,
    "title":            str,
    "has_table":        bool,
    "has_visuals":      bool,
    "vision_analyzed":  bool,
})

def parse_pptx(
    path: Path,
    enable_vision: bool = True,
    vision_provider: str | None = None,
) -> list[PPTXRecord]:
    """
    每張 slide：
    1. 提取文字
       - TITLE placeholder → title 欄位
       - 其他 text_frame → normalize_block() → 加進 text
       - notes → 附加到 text 末尾（前綴 [Notes]: ）
    2. 提取表格
       - shape.has_table → rows_to_markdown() → 獨立 kind="table" record
    3. Vision 分析
       - MSO_SHAPE_TYPE.PICTURE → pptx_slide_to_bytes() → describe_image()
       - 結果附加到 text 末尾：
         \n\n[Visual Content]\nSummary: ...\nCharts: ...\nText: ...

    注意：
    - 空 PPTX → 回傳 []
    - 開檔失敗 → raise ValueError(f"Cannot open PPTX: {path}")
    """
```

---

### `skills/parse_documents/parse.py`

```python
def parse_document(
    path: str | Path,
    doc_type: Literal["pdf", "pptx"],
    enable_vision: bool = True,
    vision_provider: str | None = None,
) -> list[dict]:
    """
    驗證 path 存在、doc_type 合法，dispatch 到 _pdf / _pptx。
    """
```

CLI：
```bash
python skills/parse_documents/parse.py \
  --file data/tsla-20231231-gen.pdf --type pdf \
  [--no-vision] [--vision-provider gemini]
# stdout: JSON array of records
# stderr: progress logs
```

---

### `skills/chunk_and_index/_embed.py`

```python
def get_model() -> SentenceTransformer:
    """lru_cache。EMBED_MODEL_NAME env，預設 BAAI/bge-small-en-v1.5。"""

def embed(texts: list[str]) -> list[list[float]]:
    """batch embed，float32。空 list → []。"""
```

---

### `skills/chunk_and_index/_rerank.py`

**職責**：CrossEncoder rerank 封裝。只在 query 時用，ingest 不需要。

```python
def get_reranker() -> CrossEncoder:
    """
    lru_cache，只載入一次。
    model: cross-encoder/ms-marco-MiniLM-L-6-v2
    本地跑，不需要 API key。
    """

def rerank(
    query: str,
    results: list[dict],
    top_k: int,
) -> list[dict]:
    """
    輸入：query 字串 + ChromaDB 回傳的 list[dict]（含 "text" 欄位）
    CrossEncoder.predict([(query, r["text"]) for r in results])
    按分數 DESC 排序，取前 top_k。
    每個 dict 加上 "rerank_score": float。
    results 為空 → 回傳 []。
    """
```

---

### `skills/chunk_and_index/_store.py`

**職責**：ChromaDB 讀寫。

```python
COLLECTION_NAME = "enterprise_docs"

def get_chroma_path() -> Path:
    """CHROMA_PATH env，預設 "chroma/"。自動建立目錄。"""

def get_collection() -> chromadb.Collection:
    """lru_cache。PersistentClient + get_or_create_collection。"""

def insert_chunks(chunks: list[dict]) -> None:
    """
    每個 chunk dict 必須有：
      "text": str           → documents
      "id": str             → ids
      其他欄位             → metadatas（str|int|float|bool only）
    用 collection.upsert()。
    """

def search(
    query_vec: list[float],
    top_k: int = 5,
    where: dict | None = None,
) -> list[dict]:
    """
    ChromaDB cosine search。
    回傳 list[dict]，每個有 id、text、score、所有 metadata 欄位。
    score = 1 - cosine_similarity，越小越相似，按 ASC 排序。
    """

def list_sources() -> list[dict]:
    """[{"source_file": str, "doc_type": str, "chunk_count": int}]"""

def has_data() -> bool:
    """collection.count() > 0"""

def reset_collection() -> None:
    """delete + get_or_create"""
```

---

### `skills/chunk_and_index/index.py`

```python
def _extract_page_range(text: str, start: int, end: int) -> tuple[int, int]:
    """從 \f[PAGE:N]\f 標記反推 page_start/page_end。找不到 → (0, 0)。"""

def _make_chunk_id(source_file: str, chunk_index: int) -> str:
    """格式：{stem}_{chunk_index:04d}，例：tsla-20231231-gen_0003"""

def index_records(
    records: list[dict],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> dict:
    """
    PDF kind="text":
      - Document(text=full_text) → SentenceSplitter(chunk_size=512, chunk_overlap=64)
      - 每個 node 用 _extract_page_range() 還原 page_start/page_end
    PPTX kind="slide" → 不切。
    kind="table" → 不切。
    所有 chunk text 一次 batch embed → insert_chunks。
    回傳 {"chunk_count": int, "source_files": list[str]}。
    """

def search_records(
    query: str,
    top_k: int = 5,
    filename: str | None = None,
    rerank: bool = True,
) -> list[dict]:
    """
    1. embed query
    2. ChromaDB 撈 top-20（rerank 用，比最終 top_k 多）
    3. rerank=True → CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2") rerank，取前 top_k
    4. rerank=False → 直接回傳 top_k
    filename 不為 None → where filter。
    """
```

---

### `mcp_server/_search.py`

```python
def run_search(
    query: str,
    top_k: int = 5,
    filename: str | None = None,
    rerank: bool = True,
) -> dict:
    """
    search_records(rerank=rerank) → 格式化。
    回傳：
    {
        "query": str,
        "reranked": bool,
        "results": [{"rank", "score", "source", "doc_type", "location",
                     "section", "title", "kind", "has_visuals", "text"}],
        "total": int,
    }
    location 格式：PDF → "Page 5-6"，PPTX → "Slide 3"
    """
```

---

### `mcp_server/server.py`

```python
@mcp.tool()
def search(query: str, top_k: int = 5) -> dict: ...

@mcp.tool()
def search_by_source(filename: str, query: str, top_k: int = 5) -> dict: ...

@mcp.tool()
def list_documents() -> dict: ...

@mcp.resource("docs://sources")
def sources_resource() -> str: ...

@mcp.custom_route("/health", methods=["GET"])
async def health() -> dict:
    return {"status": "ok", "has_data": has_data()}

mcp = FastMCP(
    name="enterprise-doc-mcp",
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000")),
    json_response=True,
    stateless_http=True,
)
```

---

### `scripts/ingest.py`

```bash
python scripts/ingest.py [--reset] [--no-vision] [--vision-provider gemini] [--skip-if-exists]
```

```
流程：
1. --reset → reset_collection()
2. --skip-if-exists + has_data() → 直接結束（Zeabur 重新部署不重跑）
3. 掃描 data/，找所有 .pdf 和 .pptx
4. 對每個檔案：parse_document() → index_records()
5. 印出總結

任何單一檔案失敗 → log error，繼續下一個。
```

---

### `tests/eval_retriever.py`

**評估策略改版（RAGAS retriever-only）：**

> 原本純關鍵字 hit-rate 會因字面差異（同義詞、數字格式、段落表述）導致「檢索其實正確但被判 miss」。
> 本專案目前只評估 retriever，因此使用 RAGAS `context_precision` / `context_recall` 作為主評分，不評估 generator 的 `faithfulness` / `answer_relevancy`。

**Layer 1：肉眼 Query**
```python
EVAL_QUERIES = [
    {
        "query": "Tesla 2023 total revenue",
        "expected_source": "tsla-20231231-gen.pdf",
        "reference": "Tesla's total revenues were $96.773 billion in 2023.",
    },
    {
        "query": "Tesla automotive segment gross margin",
        "expected_source": "tsla-20231231-gen.pdf",
        "reference": "Tesla's total automotive gross margin was 19.4% in 2023.",
    },
    {
        "query": "World Bank GDP growth forecast",
        "expected_source": "GEP-June-2024-Presentation.pptx",
        "reference": "The World Bank presentation discusses global GDP growth forecasts.",
    },
]
```

**Layer 2：Ragas Context Metrics（量化）**
```python
def run_eval(top_k: int = 5) -> dict:
    """
    回傳：
    {
        "context_precision": float,
        "context_recall": float,
        "ragas_context_score": float,
        "source_top1_rate": float,
        "results": [{"query", "context_precision", "context_recall", "top1_source", "top1_location", "top1_score"}]
    }
    """
```

**Layer 3：多樣性檢查**（run_eval 輸出後肉眼確認）
- 跨頁問題：答案橫跨兩頁的 query 有沒有命中
- 表格問題：表格 chunk 有沒有出現在結果裡
- Vision 問題：vision 分析內容有沒有被搜到

**MVP 評估門檻**
- Hard gate：`context_recall >= 0.9` 且 `source_top1_rate >= 0.8`
- Diagnostic：`context_precision` 必須輸出並記錄，用於衡量 top-k 雜訊
- Optimization target：`context_precision >= 0.8` 作為後續 rerank/top-k tuning 目標，不阻塞 MVP

執行：
```bash
python tests/eval_retriever.py
# 輸出 context_precision、context_recall 和每題 top-1 結果
```

---

## 部署設定（Zeabur）

**`zbpack.json`**
```json
{
  "build_command": "python scripts/ingest.py --skip-if-exists",
  "start_command": "python mcp_server/server.py"
}
```

Zeabur dashboard：persistent volume mount 到 `/app/chroma`

環境變數（在 Zeabur 設定）：
```bash
CHROMA_PATH=/app/chroma
VISION_PROVIDER=gemini
GEMINI_API_KEY=...
ENABLE_VISION=1
PORT=8000
```

---

## 環境變數（完整列表）

```bash
# Vision
VISION_PROVIDER=gemini
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_VISION_MODEL=gemini-2.0-flash
ANTHROPIC_VISION_MODEL=claude-haiku-4-5-20251001
OPENAI_VISION_MODEL=gpt-4o-mini
ENABLE_VISION=1

# Embedding
EMBED_MODEL_NAME=BAAI/bge-small-en-v1.5
EMBED_CACHE_DIR=.cache/embeddings

# Vector Store
CHROMA_PATH=chroma/

# MCP Server
HOST=0.0.0.0
PORT=8000
```

---

## pyproject.toml 依賴

```toml
[project]
dependencies = [
    "pymupdf>=1.27.0",
    "python-pptx>=1.0.0",
    "sentence-transformers>=3.0.0",
    "chromadb>=0.5.0",
    "llama-index-core>=0.10.0",
    "google-generativeai>=0.8.0",
    "anthropic>=0.40.0",
    "openai>=1.50.0",
    "Pillow>=10.0.0",
    "mcp[cli]>=1.27.0",
    "python-dotenv>=1.2.0",
    "httpx>=0.28.0",
]
```

---

## Phase 順序與 Commit Gate

```
Phase 0   重構: 清理依賴，建立目錄結構
Phase 1   新增: _text.py、_table.py
Phase 2   新增: _render.py
Phase 3   新增: _vision.py
Phase 4   新增: _pdf.py、_pptx.py、parse.py
Phase 5   新增: chunk_and_index（_embed、_rerank、_store、index）
Phase 6   新增: scripts/ingest.py
Phase 7   測試: eval_retriever.py，記錄 Ragas context_precision / context_recall
Phase 8   新增: mcp_server（_search、server）
Phase 9   新增: Dockerfile、zbpack.json
Phase 10  文件: README、tests/test_output.log
```

每個 phase 驗證通過並更新 `plan/runtime_control.json`、`plan/progress.md` 後，agent 必須先停止並請使用者批准 commit scope 與 commit message。禁止自動 commit；禁止未經使用者明確同意重寫 git history。

---

## Done Criteria

- [ ] `parse_document()` 正確解析 Tesla PDF（跨頁 chunk 不截斷）
- [ ] `parse_document()` 正確解析 World Bank PPTX
- [ ] 表格獨立成 chunk，不與正文混合
- [ ] Vision 分析結果附加在對應 chunk text 末尾
- [ ] `eval_retriever.py` 的 Ragas `context_recall` 與 `source_top1_rate` 達到 MVP hard gate，`context_precision` 已記錄為診斷指標
- [ ] MCP server 本地跑通，三個 tool 有回應
- [ ] `tests/test_output.log` 有驗證紀錄
- [ ] Zeabur 部署成功，`/health` 回 200
- [ ] README 有公開 URL 和示範 query
