# Phase 13 — Skill Verification Evidence

## 目標
新增可驗證證據，證明 Task 2 Skills 符合官方設計、提供清晰的使用介面、並且能被 Claude Code 成功執行。

## 實作項目
- `tests/test_claude_skills.py`（更新為符合官方模式的測試）
- `tests/skill_execution.log`（記錄實際執行證據）

## 驗證內容

### Structure Validation
- Skill frontmatter 格式合法（name, description, allowed-tools）
- 必要 sections 存在：Inputs, Outputs, Safe Execution Boundary, Commands
- Scripts 位於 `scripts/` 目錄內
- Commands section 使用 `${CLAUDE_SKILL_DIR}` 變數

### Execution Boundary (File-level)
- **格式限制**: 只處理 PDF/PPTX，reject 其他格式
- **寫入範圍**: Chroma 只寫入指定 path
- **Credential 隔離**: `--no-vision` 作為預設，external vision 為 optional
- **Source protection**: ingest 不修改 source documents

### Practical Execution
- 透過 SKILL.md 提供的命令成功執行 parse
- 透過 SKILL.md 提供的命令成功執行 index
- 執行 log 記錄完整的 command、output、和 verification

## 驗證
- `uv run python -m unittest -q tests/test_claude_skills.py` (結構與格式驗證)
- `uv run python -m unittest -q tests/test_parse_documents.py` (邊界限制驗證)
- Parse skill execution (按照 SKILL.md Commands section):
  ```bash
  uv run python .claude/skills/parse-enterprise-documents/scripts/parse.py --source-dir tests/fixtures/task2-input --no-vision
  ```
- Index skill execution (按照 SKILL.md Commands section):
  ```bash
  CHROMA_PATH=.cache/task2-skill-chroma uv run python .claude/skills/index-enterprise-documents/scripts/ingest.py --data-dir tests/fixtures/task2-input --reset --no-vision
  ```
- Index alias smoke:
  ```bash
  uv run python .claude/skills/index-enterprise-documents/scripts/ingest.py --help
  ```

## 完成條件
- 測試通過，包含結構和邊界驗證
- Scripts 可按照 SKILL.md 指引成功執行
- `tests/skill_execution.log` 記錄完整執行證據
- Log 顯示 processed_files, chunk_count, 和 successful completion
- Help text 顯示 index Skill 同時接受 `--data-dir` 與 `--source-dir`

## Commit Gate
- 驗證通過並更新進度紀錄後，必須等待使用者明確同意才可 commit。
