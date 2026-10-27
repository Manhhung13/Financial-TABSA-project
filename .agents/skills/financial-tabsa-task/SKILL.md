---
name: financial-tabsa-task
description: Execute one bounded Financial TABSA repository task (dataset audit, human Gold annotation, XLM-R stage A/B/C/D, evaluation or serving) with minimal context, reproducibility gates and a short handoff. Invoke for a task ID T-001..T-011 or when resuming a Codex session. Do not use for unrelated repositories.
---
# Financial TABSA task execution

1. Load repo `AGENTS.md`, `state/CURRENT.md`, and exactly one `tasks/T-XXX-*.md` corresponding to the user task.
2. Read only docs named in that task's `Context (read ONLY)` field; do not load the source DOCX or all plans by default.
3. Verify actual file paths before editing. Check preconditions/acceptance, then make the smallest scoped change.
4. Validate with cheap offline tests first. Expensive GPU work and new dataset downloads require explicit permission.
5. Guard invariants: LLM Silver not Gold test; aspect score 0 is ambiguous; absent != neutral; grouped/time split; verify LoRA/head transfer.
6. Update `state/HANDOFF.md` in <=12 lines and `state/CURRENT.md` only for verified status. Stop at next task boundary.

For general runbooks see `docs/sop/SOP-01-task-cycle.md`; for data `SOP-02`, training `SOP-03` and evaluation `SOP-04`. Keep final response short with paths and PASS/FAIL evidence.
