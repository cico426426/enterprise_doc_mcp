# Plan Review (2026-05-05)

## 發現的風險與可能問題

1. `mcp[cli]>=1.27.0` 版本固定為較新，若 Zeabur build 環境拉到不同次版本，HTTP transport 參數可能有行為差異。
2. `google-generativeai` 套件與新舊 Gemini API 常有遷移差異，`_vision.py` 需先確認最新官方呼叫方式再定稿。
3. `uv run pytest -q tests -k ...` 這類驗證命令在早期 phase 尚未有測試檔時會失敗，需在 phase 0/1 先補最小 smoke tests。
4. `Anthropic` 模型字串 `claude-haiku-4-5-20251001` 可能隨 API 版本調整；建議把模型名交給 env 並在啟動時檢查。
5. `scripts/ingest.py --skip-if-exists` 在資料更新但 collection 已有資料時會跳過重建，建議加入 source checksum/mtime 判斷。
6. `Phase 7` 以 `hit_rate > 0.8` 為硬門檻，資料集小時有機率波動；建議同時記錄 top-k 來源一致率與 query-level錯誤分析。

## 建議方向

1. 先完成最小可跑縱切（Phase 0~6），確保 parse->index->search 端到端可執行。
2. Vision provider 先只實作單一 provider（Gemini）與抽象介面，其他 provider 以 `NotImplemented` + 明確警告保留擴充點。
3. Phase 驗證採「存在性 + smoke test」優先，等核心流程穩定再補完整測試矩陣。
4. 在 `runtime_control.json` 中持續維護 `current_phase`，嚴格一階段一驗證，避免跨 phase 漏檢。
