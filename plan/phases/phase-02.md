# Phase 2 — Render 層

## 目標
提供 PDF 頁面與 PPTX 圖片 bytes 抽取能力，不耦合 Vision API。

## 實作項目
- `skills/parse_documents/_render.py`

## 驗證
- PDF 頁面可輸出 JPEG bytes
- PPTX 可擷取首個圖片 bytes，無圖片回傳 `None`

## 完成條件
- 錯誤行為與回傳型別符合規格
