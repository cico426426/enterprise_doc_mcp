# Phase 17 — NotebookLM Slide Deck Verification Evidence

## 目標
新增 Task 3 的可驗證輸出：測試、NotebookLM MCP run log、screenshots/snapshots/result JSON，證明 LangChain `create_agent` + Playwright MCP browser agent 成功驅動 NotebookLM browser workflow。

## 實作項目
- `tests/test_notebooklm_ppt_agent.py`
- `tests/notebooklm_ppt_agent_execution.log`
- `tests/screenshots/notebooklm-ppt-generation-started.yml`
- `tests/artifacts/notebooklm-ppt-agent-result.json`
- `tests/artifacts/notebooklm-upload-manifest.json`
- 必要時新增 source bundle fixture 或 expected outline
- LangChain `create_agent` + Playwright MCP browser agent runner，用於真實 NotebookLM UI workflow
- 不提交 `.cache/task3-notebooklm/session.json`、Google cookies、browser profile 或其他 auth state

## 驗證證據要求
- log 需包含 NotebookLM URL、輸入 source bundle、custom prompt、browser 操作步驟與完成/blocked 狀態
- screenshot 或 Playwright snapshot 需顯示 NotebookLM workflow 已被實際驅動，例如 source uploaded、Slide Deck generation started/completed、或 outline captured；不能只有空白頁或登入頁
- 測試需覆蓋成功路徑與至少一個失敗或驗證錯誤情境
- 若使用 CDP 模式，執行前需先在 Chrome 開啟一個 NotebookLM notebook 內容頁（非首頁）
- 或在 CLI 提供 `--notebook-url`，讓 agent 直接進入既有 notebook 頁面再執行 upload/generate
- 若 Slide Deck 已經開始生成，只能使用 MCP agent 的 observe 路徑記錄目前狀態，不要等待完成、重新上傳或重新生成

## 目前狀態（2026-05-09）
- 舊 selector-based Playwright runner 與 `scripts/notebooklm_ppt_agent.py` 已移除，避免再次卡在 OS 檔案管理器；live workflow 只走 LangChain `create_agent` + Microsoft Playwright MCP browser tools。
- MCP browser agent 已能建立 Notebook、上傳 `project-workflow-source.txt`，並按下 NotebookLM Slide Deck / 簡報生成按鈕。
- NotebookLM 回報「無法生成簡報，請試試其他內容」後，source bundle 已改成較短的 slide-deck brief，避免上傳大量 runtime/progress/log 原文。
- MCP agent 現在會產生 upload manifest，列出必要文字 brief 與可選 screenshot image sources，讓 browser agent 先判斷要上傳哪些來源。
- MCP agent 已加上 one-shot generation rule：必須先上傳所有選定 sources，確認來源處理完成後只能按一次 Generate；若 NotebookLM 回報無法生成，必須 stop as blocked，不可補傳圖片後再次生成。
- MCP agent 已新增 outline-first mode：先用 NotebookLM chat 產生 6-8 頁簡報大綱，不使用 Slide Deck/Generate；只有 outline 可用時才值得進一步嘗試 Slide Deck generation。
- Phase 已完成：成功 browser workflow 的 log、snapshot、result JSON、upload manifest 已保存到 `tests/` evidence 路徑。
- Generate 按鈕已被點擊且畫面進入生成中；snapshot 顯示 `正在生成簡報... 根據1 個來源` 與 `開始生成「簡報」。`
- 補充證據：使用者在 NotebookLM 生成完成後手動下載的 `tests/artifacts/EnterpriseDocMcp_Engineering_Blueprint.pptx` 已保存為 artifact；agent 不等待下載，也不把下載視為必要 gate。
- 補充執行紀錄：`tests/artifacts/task3-notebooklm-run/` 保存 sanitized browser agent run directory，包含完整 MCP log、prompt、source、manifest、result JSON、console logs 與 page snapshots；email 與本機 home path 已 redacted。

## 正確執行入口
- 完整 MCP workflow：`uv run python scripts/notebooklm_ppt_mcp_agent.py --cdp-url http://127.0.0.1:9222 --output-dir task3-notebooklm --model openai:gpt-5 --recursion-limit 80 --max-wait-minutes 5 --fresh-notebook`
- Outline-first 安全檢查：`uv run python scripts/notebooklm_ppt_mcp_agent.py --cdp-url http://127.0.0.1:9222 --output-dir task3-notebooklm --model openai:gpt-4.1 --recursion-limit 120 --fresh-notebook --outline-first`
- 已開始生成時只觀察狀態：`uv run python scripts/notebooklm_ppt_mcp_agent.py --cdp-url http://127.0.0.1:9222 --output-dir .cache/task3-notebooklm --model openai:gpt-4.1 --recursion-limit 30 --max-wait-minutes 1 --observe-existing-generation`
- 執行 log：`.cache/task3-notebooklm/notebooklm-ppt-mcp-agent.log`
- Upload manifest：`.cache/task3-notebooklm/notebooklm-upload-manifest.json`

## 驗證
- `uv run python -m unittest -q tests/test_notebooklm_ppt_agent.py`
- `rg -n 'NotebookLM|Slide Deck|generation_started|generation|screenshot|snapshot' tests/notebooklm_ppt_agent_execution.log`
- `test -s tests/screenshots/notebooklm-ppt-generation-started.yml`
- `test -s tests/artifacts/notebooklm-ppt-agent-result.json`
- `test -s tests/artifacts/notebooklm-upload-manifest.json`

## 完成條件
- Task 3 evidence 檔案已提交準備好
- 測試、log validation、screenshot/snapshot evidence、result JSON validation 都通過
- 不加入大型影片檔；只使用合理大小的 screenshot/log/result JSON 與可選 PPTX artifact

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
