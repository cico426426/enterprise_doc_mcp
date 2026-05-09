# Phase 18 — Task 3 README Documentation

## 目標
更新 README，讓 reviewer 能清楚看到 Task 3 browser automation agent 的交付物、執行方式與驗證方式。

## 實作項目
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `Dockerfile`
- `plan/runtime_control.json`
- `plan/progress.md`

## README 內容
- `Task 3: NotebookLM PPT Browser Agent`
- Task 3 專屬資料夾：`task3_notebooklm_agent/`
- agent CLI 用法
- 如何準備 source bundle
- 如何用已登入的 browser session 跑 NotebookLM Slide Deck workflow
- 手動下載的 NotebookLM `.pptx` 補充 artifact
- evidence paths：run log、snapshots、sanitized browser run directory、downloaded PPTX、structured output
- dependency boundary：Task 3 browser-agent libraries live in the `task3` dependency group, while Task 1 Docker/Zeabur deployment excludes `eval` and `task3`
- key assumptions：NotebookLM 需要登入且 UI 可能變動，因此完整外部 workflow 是 manual-assisted automation
- AI/agent workflow：說明使用 Codex/Claude Skills/MCP 任務分工

## 驗證
- `rg -n 'Task 3|NotebookLM|PPT|Slide Deck|notebooklm_ppt_mcp_agent|screenshots' README.md`
- `uv run --group task3 python -m unittest -q tests/test_notebooklm_ppt_agent.py`
- `uv lock --check`
- `python3 -m json.tool plan/runtime_control.json`
- `git diff --check`

## 完成條件
- README 可直接引導 reviewer 驗證 Task 3
- README 不宣稱 NotebookLM workflow 可在無登入 CI 中完整重跑
- Task 1 Docker/Zeabur production sync 不安裝 Task 3 NotebookLM browser-agent dependencies

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
