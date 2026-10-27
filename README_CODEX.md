# Financial TABSA - Codex operating pack

This pack adds project governance / planning files only. It does NOT train a model or replace your source code.

## Quick route
- First read: `AGENTS.md` (Codex automatically loads this when in project root).
- Current state and next action: `state/CURRENT.md`.
- Pick one task: `tasks/INDEX.md` -> `tasks/T-xxx-*.md`.
- Concepts and exact labeling policy: `docs/DOMAIN_RULES.md` and `docs/DATA_CONTRACT.md`.
- Stage pipeline and transfer: `docs/ML_DESIGN.md`, `plans/PHASE-*.md`.
- Operating checklists: `docs/sop/`.
- Model/task mapping: `docs/MODEL_ROUTING.md`.
- Optional Codex workflow skill: `.agents/skills/financial-tabsa-task/SKILL.md`.

## Safe boot
1. Inspect current git diff and file layout.
2. Ask Codex: `Read AGENTS.md, state/CURRENT.md, and tasks/T-001-repo-audit.md only. Do T-001, do not run training.`
3. Proceed T-002.. one at a time; do not automatically advance to stage A-D.

## Existing repo integration
The source report is archived in `docs/reference/source_report.docx` and summarized in short docs.
Document paths are recommended interfaces, not proof that an implementation exists. T-001 resolves actual tree first.
No raw datasets or checkpoints are bundled. Keep `.venv`, caches, secrets, GPU artifacts and raw data out of Git.

## Documentation rules
- `docs/DOMAIN_RULES.md` = business truth; `docs/DATA_CONTRACT.md` = schema truth; `docs/ML_DESIGN.md` = learning design.
- `plans/` = intended work; `tasks/` = bounded execution; `state/` = actual verified progress.
- `docs/ADR/` = approved design decisions; report conflicts go into `state/BLOCKERS.md`.
- When a requirement changes, update one canonical doc, then only link from others.

## Not automatic
The optional model pins require account access. Active agent definitions inherit the parent's model by default; only reasoning effort is set.
No Codex configuration alone can guarantee lower billed usage; short instructions, targeted reads and avoiding excess subagents reduce unnecessary context.
