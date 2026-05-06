# Phase 7 — Retriever 評估

## 目標
建立可量化搜尋效果的評估腳本。

## 實作項目
- `tests/eval_retriever.py`

## 驗證
- Layer 1 查詢可執行
- Layer 2 Ragas `context_precision` / `context_recall` 正確計算
- 輸出含每題 context scores 與 top-1 摘要

## 完成條件
- MVP hard gate：`context_recall >= 0.9` 且 `source_top1_rate >= 0.8`
- Diagnostic metric：記錄 `context_precision`，目前 baseline 可接受但不作 MVP 阻塞
- Optimization target：後續 rerank/top-k tuning 目標為 `context_precision >= 0.8`

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
