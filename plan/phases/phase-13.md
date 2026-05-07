# Phase 13 — Skill Verification Evidence

## 目標
新增可驗證證據，證明 Task 2 Skills 不只是文件，而是能對應實際 command 與輸出。

## 實作項目
- `tests/test_claude_skills.py`
- `tests/skill_output.log`

## 驗證內容
- Skill frontmatter 格式合法
- 必要 section 存在：inputs、outputs、safe execution boundary、commands
- 實際執行 parse command
- 實際執行 deployment-safe ingest command
- log 只記錄 command/output 摘要，不記錄環境變數值

## 驗證
- `uv run python -m unittest -q tests/test_claude_skills.py`
- `uv run python skills/parse_documents/parse.py --file data/GEP-June-2024-Presentation.pptx --type pptx --no-vision`
- `uv run python scripts/ingest.py --skip-if-exists --no-vision`

## 完成條件
- 測試通過
- `tests/skill_output.log` 記錄 commands、outputs、Task 2 對應關係

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
