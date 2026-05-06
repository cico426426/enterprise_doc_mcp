# Phase 0 — 重構與骨架

## 目標
建立專案目錄骨架、依賴設定與環境範本，確保後續實作有固定邊界。

## 實作項目
- 建立目錄：`skills/parse_documents`、`skills/chunk_and_index`、`mcp_server`、`scripts`、`tests`
- 更新 `pyproject.toml` 依賴
- 建立 `.env.example`

## 驗證
- 目錄結構符合 `plan/plan.md`
- `pyproject.toml` 可解析

## 完成條件
- 上述檔案與目錄存在且可讀

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
