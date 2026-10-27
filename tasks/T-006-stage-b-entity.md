# T-006: Stage B Entity
Status: TODO
Owner: implementer
Depends on: T-002,T-005 (sequential path); T-012 R6-B PASS
Context (read ONLY): plans/PHASE-B.md;docs/ML_DESIGN.md;docs/DATA_CONTRACT.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Train entity-level EN SEntFiN task with original headline grouping and 3-class head, validate A -> B weights; standalone B path for ablation.
Stage B data use is independent of Gold Pilot gates but blocked until R6-B verifies source rights, entity-label handling, parse-error quarantine and headline grouping.

## Acceptance criteria
Macro-F1 and multi-entity metrics, reproducible adapter_B and head_B plus load report.

## Minimum validation
python -m pytest tests/test_stage_b.py -q (if created)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-007.
