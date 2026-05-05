# Phase 5 — Chunk / Embed / Store / Search

## 目標
完成 index 與搜尋核心，含 rerank。

## 實作項目
- `skills/chunk_and_index/_embed.py`
- `skills/chunk_and_index/_rerank.py`
- `skills/chunk_and_index/_store.py`
- `skills/chunk_and_index/index.py`

## 驗證
- PDF text 走 SentenceSplitter
- PPTX slide、table 不切 chunk
- Chroma upsert / query / filter 可運作
- rerank 可排序並附帶分數

## 完成條件
- `index_records()` 與 `search_records()` 可端到端跑通
