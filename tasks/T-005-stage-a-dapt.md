# T-005: Stage A Dapt
Status: TODO
Owner: implementer
Depends on: T-002,T-003
Context (read ONLY): plans/PHASE-A.md;docs/ML_DESIGN.md;docs/sop/SOP-03-train-stage.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Build/reconcile Stage A MLM pretraining from Vietnamese corpus, test group split and compatibility of adapter_A with next-stage encoder.

## Acceptance criteria
MLM smoke and val, data+base hashes, measured VRAM, verified adapter portability; E1 Gold val comparable.

## Minimum validation
python scripts/05_train_stage_A_dapt.py --mode smoke (only if file confirmed and authorized)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-006.
