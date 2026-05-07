# Phase 11 — Task 2 Planning And Boundaries

## 目標
為 Task 2 建立獨立 phase plan，明確區分 Task 1 的 remote MCP server 交付與 Task 2 的 Claude Skills packaging 交付。

## Task 1 / Task 2 區分
- Task 1：把 preprocessing pipeline 包成可部署的 remote MCP server，重點是 public URL、MCP tools、retrieval demo、部署與驗證證據。
- Task 2：把同一批 preprocessing 能力整理成 Claude Code project Skills，重點是 `SKILL.md`、inputs/outputs、安全邊界、Claude Code 可探索與可執行證據。

## 後續 Phase
- Phase 12：建立 project-scoped Claude Skills。
- Phase 13：新增 Skill 驗證測試與實際執行 log。
- Phase 14：更新 README，讓面試官能清楚看到 Task 2 交付與驗證方式。

## 實作項目
- `plan/phases/phase-11.md`
- `plan/phases/phase-12.md`
- `plan/phases/phase-13.md`
- `plan/phases/phase-14.md`
- `plan/runtime_control.json`
- `plan/progress.md`

## 驗證
- `python3 -m json.tool plan/runtime_control.json`
- `rg -n 'phase-1[1-4]|Task 2|Claude Skills' plan`

## 完成條件
- `current_phase` 指向 `phase-11`
- Phase 11-14 都有明確 scope、驗證命令與 commit gate
- Phase 11 不包含 `.claude/skills` 或測試實作檔

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
