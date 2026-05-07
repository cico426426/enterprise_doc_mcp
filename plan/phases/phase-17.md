# Phase 17 — NotebookLM PPT Verification Evidence

## 目標
新增 Task 3 的可驗證輸出：測試、NotebookLM run log、screenshots、downloaded PPTX，證明 browser agent 成功驅動 NotebookLM Slide Deck workflow。

## 實作項目
- `tests/test_notebooklm_ppt_agent.py`
- `tests/notebooklm_ppt_agent_execution.log`
- `tests/screenshots/notebooklm-ppt-*.png`
- `tests/artifacts/notebooklm-project-workflow-deck.pptx` 或可重跑產生的 `.cache/task3-notebooklm/*.pptx`
- 必要時新增 source bundle fixture 或 expected outline
- 不提交 `.cache/task3-notebooklm/session.json`、Google cookies、browser profile 或其他 auth state

## 驗證證據要求
- log 需包含 NotebookLM URL、輸入 source bundle、custom prompt、browser 操作步驟、完成狀態、downloaded PPTX path
- screenshot 需顯示 NotebookLM Slide Deck 已完成或下載選單可見，而不是只有空白頁或登入頁
- downloaded `.pptx` 需存在且可由 `python-pptx` 開啟
- 測試需覆蓋成功路徑與至少一個失敗或驗證錯誤情境

## 驗證
- `uv run python -m unittest -q tests/test_notebooklm_ppt_agent.py`
- `rg -n 'NotebookLM|Slide Deck|pptx|download|completed|screenshot' tests/notebooklm_ppt_agent_execution.log`
- `test -s tests/screenshots/notebooklm-ppt-completed.png`
- `uv run python -c "from pptx import Presentation; Presentation('tests/artifacts/notebooklm-project-workflow-deck.pptx')"`

## 完成條件
- Task 3 evidence 檔案已提交準備好
- 測試、log validation、PPTX artifact validation 都通過
- 不加入大型影片檔；只使用合理大小的 screenshot/log/PPTX

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
