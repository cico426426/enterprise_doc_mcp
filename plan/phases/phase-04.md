# Phase 4 — 文件解析主流程

## 目標
完成 PDF / PPTX 解析與 dispatch，輸出統一 records。

## 實作項目
- `skills/parse_documents/_pdf.py`
- `skills/parse_documents/_pptx.py`
- `skills/parse_documents/parse.py`

## 驗證
- PDF 跨頁頁碼標記可插入
- 表格為獨立 record
- Vision 附加段落格式固定
- CLI 參數可用

## 完成條件
- 對 `data/` 內兩份檔案可成功輸出 JSON records

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
