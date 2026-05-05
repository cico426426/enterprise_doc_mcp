# Phase 6 — Ingest 腳本

## 目標
建立可重複執行且容錯的 ingest CLI。

## 實作項目
- `scripts/ingest.py`

## 驗證
- `--reset`、`--skip-if-exists`、`--no-vision` 生效
- 單一檔案失敗不中斷整批

## 完成條件
- ingest 後 Chroma 有資料，摘要輸出正確
