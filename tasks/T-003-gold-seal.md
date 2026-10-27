# T-003: Gold Seal
Status: TODO
Owner: data_worker
Depends on: T-002 (T-003A design); T-012 R1-R3 PASS (T-003B annotation-data execution/seal)
Context (read ONLY): docs/DOMAIN_RULES.md;docs/DATA_CONTRACT.md;docs/ADR/ADR-0003-chronological-splits.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Draft annotation guideline, generate review queue, collect actual verified Gold, split by event/time and seal test. Do not auto-promote Silver.

## Bounded lanes and execution gates
- **T-003A — Annotation design only:** may proceed after T-002 using project contracts and guidelines without T-012 completion, dataset row inspection, or source-data sampling. Output schema/rubric, reviewer protocol, adjudication rules and a data-independent review-queue specification.
- **T-003B — Annotation-data execution and Gold seal:** start only for sources with T-012 R1 rights PASS, targets with R2 identity PASS, and candidate rows with R3 grouping PASS. If Silver supplies candidates, also require R4 PASS for that source. If automated scripts are used, require R5 runtime PASS. Exclude blocked sources/targets; do not invent mappings or labels.
- Stage B/C readiness is independent: T-012 R6-B and R6-C gate their respective training tasks, not T-003A or an otherwise-valid Gold Pilot.
- Gold-test decontamination for Stage A is performed only after the Gold split is sealed; never use test labels for preprocessing or tuning.

## Acceptance criteria
Verified Gold schema and grouping manifest, no leakage, test sealed; otherwise BLOCKED pending human review.

## Minimum validation
python -m pytest tests/test_gold_split.py -q (if created)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-004.
