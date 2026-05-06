# Phase 3 — Vision 分析封裝

## 目標
建立可替換 provider 的影像描述介面，失敗可降級。

## 實作項目
- `skills/parse_documents/_vision.py`

## 驗證
- provider 決策順序：參數 > env > 預設
- 空 bytes、網路錯誤、JSON 錯誤均回傳 `None`
- warning log 需遮罩 API key

## 完成條件
- 回傳 schema 與 prompt 固定格式符合規格

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
