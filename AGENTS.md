# Repository Agent Rules

## Phase Execution Contract

For every phase in `plan/runtime_control.json`, the agent must run this sequence:

1. Load `current_phase` and read its `phase_path`.
2. Implement only the scoped phase work.
3. Run `implementation_check.validation_commands`.
4. Update phase status and check fields in `plan/runtime_control.json`.
5. Append a conformance record to `plan/progress.md`.
6. Stop and ask the user for explicit approval before creating any commit.
7. Commit only after the user approves the exact commit scope/message.

## Commit Policy (Mandatory)

- Do not batch multiple completed phases into one commit.
- One completed phase should produce one focused commit.
- Never commit automatically. User approval is required for every commit.
- If validation fails, do not commit and mark the phase as `blocked` or `in_progress` with notes.
- Do not rewrite git history unless the user explicitly approves the exact history operation after seeing the current log and risks.
