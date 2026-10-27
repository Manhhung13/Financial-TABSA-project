# Copy-ready prompts for Codex (Vietnamese user can paste as-is)

## Initial setup / T-001 (cheap, read-only)
Read `AGENTS.md`, `state/CURRENT.md`, and `tasks/T-001-repo-audit.md` only. Do T-001 read-only. Return a <=12-line inventory with actual file paths and blockers. No code edits, package installs, downloads or GPU jobs. Update handoff only if authorized.

## Next bounded task
Execute only task T-002 from `tasks/T-002-data-audit.md`. Follow AGENTS.md, read only Context links, make the minimum patch, run smallest applicable tests and update state/HANDOFF.md. Do NOT start T-003 automatically.

## Expensive task request (approval gate)
Evaluate feasibility of T-005 Stage A DAPT from existing code/data without starting training. Return smoke command, expected VRAM constraints, paths and stop conditions. Do not execute a large job until I explicitly approve.

## Two-agent bounded review
Delegate scout to find relevant repo entrypoints (read-only) and reviewer to inspect data leakage rules (read-only), with task ID T-003 and linked docs only. Wait for short summaries and consolidate a single actionable checklist. Do not spawn more than two.

## Handoff after session reset
Read `AGENTS.md`, `state/CURRENT.md`, `state/HANDOFF.md`, then ONLY the active task file. Do not scan other docs. Tell me what is verified and the next small action.
