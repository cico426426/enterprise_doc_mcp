# Phase 12 — Claude Skills Packaging

## 目標
把既有 preprocessing modules 包裝成 Claude Code project Skills，提供清晰的使用介面、執行指引、和安全執行邊界，讓 Claude Code 可以透過 SKILL.md 指引成功執行 preprocessing 任務。

## 實作項目
- `.claude/skills/parse-enterprise-documents/SKILL.md`
- `.claude/skills/parse-enterprise-documents/scripts/parse.py`（從 `skills/parse_documents/parse.py` 移動或 symlink）
- `.claude/skills/index-enterprise-documents/SKILL.md`
- `.claude/skills/index-enterprise-documents/scripts/ingest.py`（從 `scripts/ingest.py` 移動或 symlink）

## Skill 要求（符合官方模式）

### Frontmatter
- 必須有合法 `name` 和 `description`
- `description` 應說明 what 和 when to use
- 使用 `allowed-tools: Bash(uv run python *)` 預先授權執行，確保命令跑在專案 uv dependency environment 內
- 可選：`disable-model-invocation: true` 用於需要手動觸發的任務

### Content Structure
- **Inputs section**: 說明所有參數、flags、環境變數
- **Outputs section**: 說明輸出格式、寫入位置
- **Safe Execution Boundary**: 說明檔案格式限制、寫入範圍、credential 要求
- **Commands section**: 提供具體執行範例，使用 `${CLAUDE_SKILL_DIR}` 變數
- Index Skill 需明確說明：建立索引時只跑 index Skill，不先跑 parse Skill
- Index Skill 接受 `--source-dir` 作為 `--data-dir` alias，避免 Claude 從 parse Skill 記錯參數後中斷

### Scripts Organization
- Scripts 位於 `${CLAUDE_SKILL_DIR}/scripts/` 內
- SKILL.md 提供完整執行命令，包含參數範例
- Claude 讀取 SKILL.md 後用 Bash tool 執行指定命令

### 安全邊界實作（檔案層級）
- **格式限制**: 只接受 PDF/PPTX，拒絕其他格式
- **寫入控制**: Chroma 只寫入指定 path，ingest 不修改 source files
- **Credential 隔離**: Vision 為 optional，使用 `--no-vision` 作為 public demo 預設值
- **不改變 Task 1**: 只包裝現有能力，不修改 MCP server 行為

## 驗證
- `rg -n 'name:|description:|Inputs|Outputs|Safe Execution Boundary|Commands' .claude/skills/*/SKILL.md`
- `find .claude/skills/*/scripts -name "*.py" -type f` (確認 scripts 在正確位置)
- `rg '\${CLAUDE_SKILL_DIR}' .claude/skills/*/SKILL.md` (確認使用官方變數)
- `rg -l 'allowed-tools:.*Bash' .claude/skills/*/SKILL.md` (確認預先授權設定)

## 完成條件
- Claude Code project Skills 可由 `.claude/skills/*/SKILL.md` 探索
- Scripts 位於各 Skill 的 `scripts/` 目錄內
- SKILL.md 包含清晰的執行命令範例
- Commands section 使用 `${CLAUDE_SKILL_DIR}/scripts/` 引用

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
