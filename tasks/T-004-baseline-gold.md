# T-004: Baseline Gold
Status: TODO
Owner: implementer
Depends on: T-003
Context (read ONLY): docs/ML_DESIGN.md;plans/PHASE-D.md;docs/RESEARCH_PROTOCOL.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Run tiny Gold-only XLM-R two-head baseline first, LoRA on 6GB, training only after smoke approval.

## Acceptance criteria
Reproducible E0 val metrics, checkpoint manifest, VRAM; no claimed test metric pre-freeze.

## Minimum validation
python -m pytest tests/test_model_forward.py -q (if created)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-005.
