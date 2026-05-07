# Phase 18 — Task 3 README Documentation

## 目標
更新 README，讓面試官能清楚看到 Task 3 browser automation agent 的交付物、執行方式與驗證方式。

## 實作項目
- `README.md`
- `plan/runtime_control.json`
- `plan/progress.md`

## README 內容
- `Task 3: NotebookLM PPT Browser Agent`
- Task 3 專屬資料夾：`task3_notebooklm_agent/`
- agent CLI 用法
- 如何準備 source bundle
- 如何用已登入的 browser session 跑 NotebookLM Slide Deck workflow
- 如何下載並驗證 NotebookLM `.pptx`
- evidence paths：run log、screenshots、downloaded PPTX、structured output
- key assumptions：NotebookLM 需要登入且 UI 可能變動，因此完整外部 workflow 是 manual-assisted automation
- AI/agent workflow：說明使用 Codex/Claude Skills/MCP 任務分工

## 驗證
- `rg -n 'Task 3|NotebookLM|PPT|Slide Deck|notebooklm_ppt_agent|screenshots' README.md`
- `python3 -m json.tool plan/runtime_control.json`

## 完成條件
- README 可直接引導面試官驗證 Task 3
- README 不宣稱 NotebookLM workflow 可在無登入 CI 中完整重跑

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
