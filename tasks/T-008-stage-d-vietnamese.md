# T-008: Stage D Vietnamese
Status: TODO
Owner: implementer
Depends on: T-003,T-004,T-007
Context (read ONLY): plans/PHASE-D.md;docs/DOMAIN_RULES.md;docs/ML_DESIGN.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Fine-tune Vietnamese Gold TABSA with presence and conditional sentiment heads, null/masked labels, target-aspect pair.

## Acceptance criteria
Saved final model, human Gold val metrics and per-aspect errors, no Gold test tuning.

## Minimum validation
python -m pytest tests/test_stage_d.py -q (if created)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-009.
