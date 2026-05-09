# Phase 16 — NotebookLM PPT Browser Agent

## 目標
實作 NotebookLM PPT browser agent 的基礎結構：準備專案 source bundle，建立 NotebookLM prompt，並提供 LangChain `create_agent` + Playwright MCP 的 live browser automation 入口。

## 實作項目
- `task3_notebooklm_agent/__init__.py`
- `task3_notebooklm_agent/config.py`
- `task3_notebooklm_agent/source_bundle.py`
- `task3_notebooklm_agent/mcp_agent.py`（live Browser Agent）
- `scripts/notebooklm_ppt_mcp_agent.py`（主要 live Browser Agent CLI）
- Project source bundle generator
- NotebookLM prompt template
- 可設定輸出路徑、CDP endpoint、model、recursion limit
- 產出 JSON result 與 MCP run log，記錄 source bundle、prompt、download path、status

## 設計要求
- 使用真實 NotebookLM browser workflow
- live workflow 必須透過 Microsoft Playwright MCP browser tools，由 LangChain `create_agent` 操作 NotebookLM UI
- 預設支援 CDP 連接已登入 Chrome，讓使用者可用既有 Google 登入 session
- 不使用 confidential material
- source bundle 只包含 repo 中可公開的 README、plan、logs 摘要，不上傳 `.env` 或 credentials
- browser workflow 必須由 agent 實際操作 NotebookLM UI，而不是直接寫 PPTX 假裝完成
- 若 NotebookLM UI 暫時只提供 PDF 或下載選單文字變動，需在 log 中記錄 fallback/blocked 狀態
- session/auth state 必須寫到 `.cache/task3-notebooklm/` 或 `playwright/.auth/`，並由 `.gitignore` 排除
- 若使用第三方 browser automation library，實作前需查官方文件並記錄依據
- 舊 selector-based Playwright runner 不可作為 live workflow，避免卡在 OS file manager
- 不保留 `scripts/notebooklm_ppt_agent.py`，避免使用者誤跑舊入口

## 驗證
- `uv run python -m unittest -q tests/test_notebooklm_ppt_agent.py`
- `uv run python scripts/notebooklm_ppt_mcp_agent.py --help`
- `uv run python -m py_compile task3_notebooklm_agent/config.py task3_notebooklm_agent/source_bundle.py task3_notebooklm_agent/mcp_agent.py scripts/notebooklm_ppt_mcp_agent.py`

## 完成條件
- agent CLI 可執行
- source bundle 與 NotebookLM prompt 可產生
- MCP agent 能啟動 NotebookLM browser workflow 的可觀測步驟
- structured output 可指出 workflow 狀態、source bundle、download path 與截圖位置

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
