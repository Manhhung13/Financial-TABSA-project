# T-007: Stage C Thai
Status: TODO
Owner: implementer
Depends on: T-002,T-006 (sequential path); T-012 R6-C PASS
Context (read ONLY): plans/PHASE-C.md;docs/DOMAIN_RULES.md;docs/ML_DESIGN.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Inspect actual Thai label cardinality before coding; implement appropriate aspect+polarity heads, and verified B -> C adapter transfer.
Stage C data use is independent of Gold Pilot gates but blocked until R6-C reviews source rights, row granularity, all 16 Thai aspect meanings and sentiment labels with explicit mapped/unmapped decisions.

## Acceptance criteria
Thai task metric table, semantic label mapping review, adapter_C/head_C manifests.

## Minimum validation
python -m pytest tests/test_stage_c.py -q (if created)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-008.
