# Phase 12 — Claude Skills Packaging

## 目標
把既有 preprocessing modules 包裝成 Claude Code project Skills，讓 agent 能探索並依照 Skill 指令呼叫 parser/index workflow。

## 實作項目
- `.claude/skills/parse-enterprise-documents/SKILL.md`
- `.claude/skills/index-enterprise-documents/SKILL.md`

## Skill 要求
- frontmatter 必須有合法 `name` / `description`
- 說明 inputs、outputs、safe execution boundary、commands
- public demo 預設使用 `--no-vision`
- external vision credentials 為 optional，只有在使用者明確設定時才啟用
- 只包裝現有 parser/index 能力，不改 Task 1 MCP server 行為

## 驗證
- `rg -n 'name:|description:|Inputs|Outputs|Safe Execution Boundary|uv run python|--no-vision' .claude/skills`

## 完成條件
- Claude Code project Skills 可由 `.claude/skills/*/SKILL.md` 探索
- Skill 文件能清楚指引 parser 與 indexing workflow

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
