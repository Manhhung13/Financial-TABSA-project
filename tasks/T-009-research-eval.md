# T-009: Research Eval
Status: TODO
Owner: reviewer
Depends on: T-004,T-005,T-006,T-007,T-008
Context (read ONLY): docs/RESEARCH_PROTOCOL.md;docs/sop/SOP-04-evaluation.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Verify E0..E6 comparison apples-to-apples, freeze chosen model, run final Gold test once after review.

## Acceptance criteria
Signed experiment table with data versions, CIs/variance if repeated, error breakdown and caveats.

## Minimum validation
python -m pytest tests/test_eval_protocol.py -q (if created)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-010.
