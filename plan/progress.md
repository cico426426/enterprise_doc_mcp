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
| 2026-05-07 | phase-11 | completed | `python3 -m json.tool plan/runtime_control.json` passed; `rg -n 'phase-1[1-4]\|Task 2\|Claude Skills' plan` passed | Task 2 phase plan established: phase-12 Skill files, phase-13 verification evidence, phase-14 README documentation. `current_phase` advanced to phase-12;未 commit，等待使用者同意 |
| 2026-05-07 | phase-11 | in_progress | Phase 11-14 plan files created and `current_phase` advanced to phase-11 | Task 2 planning only: separate Task 1 remote MCP delivery from Task 2 Claude Skills packaging; implementation will happen in phases 12-14;未 commit，等待使用者同意 |
| 2026-05-07 | phase-10 | completed | README public MCP demo queries updated; validation command pending rerun | Added interviewer-facing query path for public MCP demo: document list, World Bank growth/downside risks, Tesla revenue, Tesla litigation/product liability;未 commit，等待使用者同意 |
| 2026-05-07 | phase-10 | completed | Public URL `https://enterprise-doc-mcp-yonghuei.zeabur.app/` is reachable; `/health` returned `{"status":"ok","has_data":true}`; `README.md` validation passed | Zeabur deployment is data-ready with persistent `/app/chroma`; `tests/test_output.log` records final public health check; phase-10 completed;未 commit，等待使用者同意 |
| 2026-05-07 | phase-10 | in_progress | Public URL `https://enterprise-doc-mcp-yonghuei.zeabur.app/` is reachable; `/health` returned `{"status":"ok","has_data":false}` | Zeabur Docker service is live but initial volume has no Chroma index. Added `scripts/start_server.py` and changed Docker `CMD` so startup ingest runs with `skip_if_exists=True` before MCP server launch. Phase remains in_progress until redeploy returns `has_data:true`;未 commit，等待使用者同意 |
| 2026-05-06 | phase-10 | in_progress | `README.md` 與 `tests/test_output.log` 已補齊；`rg -n 'how to run|verify|assumption|AI' README.md` 通過 | README 已含本機執行、驗證、假設、AI workflow、Docker、Cline、Zeabur 設定；公開 Zeabur URL 尚未產生，因此 phase-10 尚未標 completed；未 commit，等待使用者同意 |
| 2026-05-06 | phase-09 | completed | `Dockerfile` 與 `zbpack.json` 已完成；`cat zbpack.json` 與 JSON parse 通過；`scripts/ingest.py --help`、deploy target py_compile 通過；Docker build/run smoke 通過 | `ragas` 已移到 `eval` dependency group，Docker production sync 使用 `--no-group eval` 避免安裝 eval-only heavy deps；`docker build -t enterprise-doc-mcp .` 成功；container `/health` 回 `{"status":"ok","has_data":true}`；MCP client 可列出 tools 並成功呼叫 `list_documents`；`current_phase` 已推進至 `phase-10`；未 commit，等待使用者同意 |
| 2026-05-06 | phase-08 | completed | `mcp_server/_search.py` 與 `mcp_server/server.py` 已完成；`tests/test_mcp_server.py` 4 tests 全過；server import/py_compile 通過 | `uv run python mcp_server/server.py` 可啟動；`/health` 回 `{"status":"ok","has_data":true}`；MCP streamable HTTP client 可列出 `search` / `search_by_source` / `list_documents` 並呼叫 `list_documents`；未 commit，等待使用者同意 |
| 2026-05-06 | phase-07-ragas | completed | `tests/eval_retriever.py` 已改為 Ragas context judge；只評估 retriever 需要的 `context_precision` / `context_recall`；`tests/test_eval_retriever.py` 3 tests 全過；live eval 成功 | MVP hard gate 改為 context_recall>=0.9 與 source_top1_rate>=0.8；live Ragas eval：context_precision=0.5528、context_recall=1.0、source_top1_rate=1.0；precision 作後續 tuning target；未 commit，等待使用者同意 |
| 2026-05-06 | commit-policy-update | completed | `AGENTS.md`、`runtime_control.json`、`plan/plan.md` 與所有 `plan/phases/phase-*.md` 已改為 commit 前需使用者明確同意 | 本次僅更新流程規則；未 commit；git history 調整需另行取得明確指令與批准 |
| 2026-05-05 | phase-07 | completed | `tests/eval_retriever.py` 已完成（固定 query、hit_rate、run_eval、JSON output）；`tests/test_eval_retriever.py` 3 tests 全過 | live eval 已可執行並產生有效分數；後續會持續優化評估方法與檢索品質；`current_phase` 已推進至 `phase-08` |
| 2026-05-05 | phase-06 | completed | `scripts/ingest.py` 已完成，`--help` 與 `tests/test_ingest.py` 皆通過 | 實際 ingest 嘗試受環境 DNS 限制（無法下載 embedding 模型），已記錄風險並推進至 `phase-07` |
| 2026-05-05 | phase-05 | completed | `_embed.py` / `_rerank.py` / `_store.py` / `index.py` 已完成；`tests/test_index_store.py` 6 tests 全過 | `current_phase` 已推進至 `phase-06` |
| 2026-05-05 | phase-04 | completed | `_pdf.py` / `_pptx.py` / `parse.py` 已完成；CLI help 正常；真實資料 smoke：PDF=65、PPTX=13 records | `current_phase` 已推進至 `phase-05` |
| 2026-05-05 | phase-03 | completed | `_vision.py` 已實作 provider 決策、API key 動態讀取、失敗降級；`tests/test_vision.py` 6 tests 全過 | `current_phase` 已推進至 `phase-04` |
| 2026-05-05 | phase-02 | completed | `_render.py` 已實作；`tests/test_render.py` 4 tests 全過；型別與錯誤行為符合規格 | `current_phase` 已推進至 `phase-03` |
| 2026-05-05 | phase-01 | completed | `_text.py` / `_table.py` 介面已對齊規格；`tests/test_text_table.py` 6 tests 全過 | `current_phase` 已推進至 `phase-02` |
| 2026-05-05 | phase-00 | completed | 相依套件已補齊；目錄骨架與 `.env.example` 已建立；`runtime_control.json` phase-00 檢查欄位已更新 | `current_phase` 已推進至 `phase-01` |
| 2026-05-05 | policy-hardening | superseded | `AGENTS.md` 新增 phase commit 合約，`runtime_control.json` 新增 commit_policy/workflow_rules | 原「每個 completed phase 立即 commit」已於 2026-05-06 改為「每次 commit 均需使用者明確同意」 |
| 2026-05-05 | planning-bootstrap | completed | 檢查 `plan/phases/*.md` 與 `runtime_control.json` 對應一致，JSON 驗證通過 | 已建立分階段計畫、動態載入入口與進度控管機制 |
| 2026-05-05 | phase-08 ~ phase-10 | pending | N/A | 尚未開始功能實作 |
