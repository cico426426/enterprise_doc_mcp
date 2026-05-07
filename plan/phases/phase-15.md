# Phase 15 — Task 3 Planning And Boundaries

## 目標
為 Task 3 建立獨立 phase plan，明確定義 browser automation agent 的交付範圍、驗證證據與限制。

## Task 3 範圍
根據 `plan/task.txt`：
- Build an agent that can reliably drive a browser workflow
- Workflow 可為 NotebookLM slide generation 或其他一般 browser task
- 必須提供 verifiable outputs 和 run logs

## Task 3 實作策略
本專案採用 NotebookLM 的真實 browser workflow：
- Browser agent 開啟 NotebookLM
- 使用本機已登入的 Google / NotebookLM session
- 建立或開啟 notebook
- 上傳或貼入本專案整理後的 source bundle
- 在 Studio panel 產生 Slide Deck
- 下載 NotebookLM 產出的 PowerPoint `.pptx`
- 保存 screenshot、run log、downloaded PPTX，作為 Task 3 驗證證據

Task 3 程式碼會獨立放在 `task3_notebooklm_agent/`，避免和 Task 1 的 MCP server、Task 2 的 Claude Skills 混在一起。

PPT 內容是本專案的工程流程展示：
- 專案目標與三個 task 的關係
- Task 1 remote MCP server architecture
- Task 2 Claude Skills packaging
- Codex phase-based implementation workflow
- Human-AI collaboration and validation loop
- Tests, logs, screenshots, deployment evidence

NotebookLM 需要登入且 UI 可能變動，因此 Task 3 會採用 manual-assisted browser automation：可由 agent 自動操作 browser，但 validation 需保留 screenshots、run log、downloaded `.pptx`，而不是宣稱可在 CI 裡無登入重跑完整外部流程。

## 後續 Phase
- Phase 16：實作 NotebookLM PPT browser agent 與 project source bundle 產生流程。
- Phase 17：新增 NotebookLM run logs、screenshots、downloaded `.pptx` 等驗證證據。
- Phase 18：更新 README，說明 Task 3 如何執行、驗證與 AI workflow。

## Task 3 專屬結構
- `task3_notebooklm_agent/`: Task 3 package，包含 auth、config、source bundle、browser automation logic
- `scripts/notebooklm_ppt_agent.py`: thin CLI entry point
- `.cache/task3-notebooklm/`: local generated source bundle、session/auth state、download outputs
- `tests/test_notebooklm_ppt_agent.py`: unit tests for source preparation、CLI validation、artifact validation
- `tests/notebooklm_ppt_agent_execution.log`: real NotebookLM run log
- `tests/screenshots/notebooklm-ppt-*.png`: browser evidence
- `tests/artifacts/notebooklm-project-workflow-deck.pptx`: downloaded PPTX evidence, if size is acceptable for git

## 實作項目
- `plan/phases/phase-15.md`
- `plan/phases/phase-16.md`
- `plan/phases/phase-17.md`
- `plan/phases/phase-18.md`
- `plan/runtime_control.json`
- `plan/progress.md`

## 驗證
- `python3 -m json.tool plan/runtime_control.json`
- `rg -n 'phase-1[5-8]|Task 3|NotebookLM|PPT|Slide Deck|browser workflow' plan`

## 完成條件
- `current_phase` 推進到 `phase-16`
- Phase 15-18 都有明確 scope、驗證命令與 commit gate
- Phase 15 不包含 browser agent 實作檔

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
