# Phase 8 — MCP Server

## 目標
提供可被外部 agent 呼叫的搜尋工具與資源。

## 實作項目
- `mcp_server/_search.py`
- `mcp_server/server.py`

## 驗證
- `search` / `search_by_source` / `list_documents` 可回應
- `/health` 回 `{"status":"ok"...}`

## 完成條件
- 本地 HTTP 模式可被 client script 成功呼叫
