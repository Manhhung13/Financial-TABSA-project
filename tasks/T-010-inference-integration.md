# T-010: Inference Integration
Status: TODO
Owner: implementer
Depends on: T-008,T-009
Context (read ONLY): docs/ARCHITECTURE.md;docs/sop/SOP-05-release.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Integrate validated model into existing FastAPI only after inspecting actual endpoints and contracts.

## Acceptance criteria
API schema/negative cases tested, model version logged, rollback plan, no surprise GPU runs.

## Minimum validation
python -m pytest tests/test_inference_api.py -q (if created)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-011.
