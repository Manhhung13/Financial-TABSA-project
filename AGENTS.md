# Financial TABSA - Codex entrypoint (read this first, keep lean)

Project: Vietnamese financial news target-aspect sentiment analysis using XLM-R.
Workspace (user): Windows PowerShell, D:\financial-tabsa; RTX 4050 6 GB VRAM / 16 GB RAM.

## Loading order (minimum context)
1. Read `state/CURRENT.md` and the ONE active task file in `tasks/`.
2. Read only task-linked docs from `docs/` and the closest applicable `AGENTS.md`.
3. Before editing code: inspect actual repository paths/symbols with targeted search. Do not assume code mentioned in planning documents exists.
4. Execute smallest change, run narrowly scoped checks, then update `state/CURRENT.md` and `state/HANDOFF.md` (<= 12 lines).
5. Never re-read the entire source report unless the task is to resolve an explicit requirements conflict.

## Non-negotiable invariants
- Task target: `(context, target_company, aspect) -> (aspect_present, sentiment_if_present)`.
- Five aspects: `business_financials`, `leadership_insider`, `macro_policy`, `capital_structure`, `legal_esg`.
- ABSENT is not NEUTRAL; score==0 in LLM labels does not prove either.
- `phobert_dataset.csv` (1,630 LLM-labeled rows) is SILVER, not an authoritative Gold test.
- Never train on or inspect Gold TEST labels to tune training, prompting, DAPT, thresholds, or model selection.
- Split by article/event BEFORE expanding into target-aspect pairs. Exclude train/eval contamination.
- Stage A MLM, B entity sentiment, C Thai aspect/sentiment, D Vietnamese Gold are DISTINCT tasks. Check head/adapter compatibility before transitions.
- Windows-only execution by default; no WSL, GPU downloads, full training or package upgrades without explicit task authorization.
- Never modify raw data, committed Gold labels, or existing checkpoints in place. No invented F1 or training outcomes.

## Delegation & token discipline
- Parent agent owns requirements, edits coordination, acceptance and final handoff.
- Use `scout` for read-only discovery; `data_worker` for data code; `ml_architect` for hard ML choices; `implementer` for scoped code; `reviewer` for read-only gate checks.
- Delegate only independent bounded work; max 2 parallel subagents; avoid spawning for trivial tasks.
- Prefer file paths + line spans, summaries <= 12 lines. Never paste large files/logs back to the parent.
- Consult `docs/MODEL_ROUTING.md` only when delegation or model choice is needed.

## Definition of done
Task acceptance satisfied; tests and reproducibility evidence recorded (or blockers documented); no unapproved dataset mutation; state/handoff updated. See `docs/sop/SOP-01-task-cycle.md`.
