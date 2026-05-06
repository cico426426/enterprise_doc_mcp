# Progress Control Log

## 使用規則
- 每次開始工作先讀：`plan/runtime_control.json`
- 根據 `current_phase` 載入對應 `phase_path`
- 實作完成後，必須執行該 phase 的 `implementation_check.validation_commands`
- 驗證通過才可把狀態改為 `completed`

## 狀態定義
- `pending`: 尚未開始
- `in_progress`: 進行中
- `completed`: 已完成且已驗證
- `blocked`: 受阻（需附原因）

## 執行紀錄

| Date | Phase | Status | Plan Conformance Check | Notes |
|---|---|---|---|---|
| 2026-05-05 | phase-07 | completed | `tests/eval_retriever.py` 已完成（固定 query、hit_rate、run_eval、JSON output）；`tests/test_eval_retriever.py` 3 tests 全過 | live eval 可執行但受 DNS 限制無法下載 embedding model，當前 hit_rate=0.0；`current_phase` 已推進至 `phase-08` |
| 2026-05-05 | phase-06 | completed | `scripts/ingest.py` 已完成，`--help` 與 `tests/test_ingest.py` 皆通過 | 實際 ingest 嘗試受環境 DNS 限制（無法下載 embedding 模型），已記錄風險並推進至 `phase-07` |
| 2026-05-05 | phase-05 | completed | `_embed.py` / `_rerank.py` / `_store.py` / `index.py` 已完成；`tests/test_index_store.py` 6 tests 全過 | `current_phase` 已推進至 `phase-06` |
| 2026-05-05 | phase-04 | completed | `_pdf.py` / `_pptx.py` / `parse.py` 已完成；CLI help 正常；真實資料 smoke：PDF=65、PPTX=13 records | `current_phase` 已推進至 `phase-05` |
| 2026-05-05 | phase-03 | completed | `_vision.py` 已實作 provider 決策、API key 動態讀取、失敗降級；`tests/test_vision.py` 6 tests 全過 | `current_phase` 已推進至 `phase-04` |
| 2026-05-05 | phase-02 | completed | `_render.py` 已實作；`tests/test_render.py` 4 tests 全過；型別與錯誤行為符合規格 | `current_phase` 已推進至 `phase-03` |
| 2026-05-05 | phase-01 | completed | `_text.py` / `_table.py` 介面已對齊規格；`tests/test_text_table.py` 6 tests 全過 | `current_phase` 已推進至 `phase-02` |
| 2026-05-05 | phase-00 | completed | 相依套件已補齊；目錄骨架與 `.env.example` 已建立；`runtime_control.json` phase-00 檢查欄位已更新 | `current_phase` 已推進至 `phase-01` |
| 2026-05-05 | policy-hardening | completed | `AGENTS.md` 新增 phase commit 合約，`runtime_control.json` 新增 commit_policy/workflow_rules | 後續採「每個 completed phase 立即 commit」 |
| 2026-05-05 | planning-bootstrap | completed | 檢查 `plan/phases/*.md` 與 `runtime_control.json` 對應一致，JSON 驗證通過 | 已建立分階段計畫、動態載入入口與進度控管機制 |
| 2026-05-05 | phase-08 ~ phase-10 | pending | N/A | 尚未開始功能實作 |
