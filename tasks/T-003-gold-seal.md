# T-003: Gold Seal
Status: T-003A DONE (design only, 2026-10-27); T-003B BLOCKED; overall Gold seal acceptance unmet
Owner: data_worker
Depends on: T-002 (T-003A design); T-012 R1-R3 PASS (T-003B annotation-data execution/seal)
Context (read ONLY): docs/DOMAIN_RULES.md;docs/DATA_CONTRACT.md;docs/ADR/ADR-0004-grouped-nontemporal-gold-splits.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Draft annotation guideline, generate review queue, collect actual verified Vietnamese Gold, split by verified article/document-family/event groups (NOT by publication time) and seal test. Do not auto-promote Silver.

## Bounded lanes and execution gates
- **T-003A — Annotation design only:** may proceed after T-002 using project contracts and guidelines without T-012 completion, dataset row inspection, or source-data sampling. Output schema/rubric, reviewer protocol, adjudication rules and a data-independent review-queue specification.
- **T-003B — Annotation-data execution and Gold seal:** start only for sources with T-012 R1 rights PASS, targets with R2 identity PASS, and candidate rows with R3 grouping PASS. If Silver supplies candidates, also require R4 PASS for that source. If automated scripts are used, require R5 runtime PASS. Exclude blocked sources/targets; do not invent mappings or labels.
- Stage B/C readiness is independent: T-012 R6-B and R6-C gate their respective training tasks, not T-003A or an otherwise-valid Gold Pilot.
- `published_at` and `first_seen_at` are OPTIONAL and may remain null; missing publication dates do not block Gold split. Do not infer dates from article text or source order.
- Assign entire adjudicated document/event groups to deterministic seeded train/val/test partitions BEFORE expanding to company-aspect pairs. Record a frozen group membership manifest, split seed, sample counts and leakage checks; unresolved event duplicates remain quarantined.
- Gold-test decontamination for Stage A is performed only after the Gold split is sealed; never use test labels for preprocessing or tuning.

## Acceptance criteria
Verified Gold schema and human labels; immutable grouped, non-temporal train/val/test manifest with no shared article/event group across splits; test sealed. Missing dates alone are NOT a blocker. Otherwise BLOCKED pending human review or source/use gates.

## Minimum validation
python -m pytest tests/test_gold_split.py -q (if created)

## T-003A design evidence (2026-10-27)
- Protocol: docs/GOLD_PILOT_PROTOCOL.md; structural rules: docs/GOLD_RECORD.schema.json.
- Invented fixtures only: docs/GOLD_SYNTHETIC_EXAMPLES.json (10 records; quarantine-only).
- Conda base Python 3.13.12 + existing jsonschema: Draft 2020-12 self-check PASS; 10 valid fixtures and 19 invalid mutations checked; fixture hashes/IDs/quotes/isolation PASS.
- No split validator created or run; no actual source rows inspected, queue generated, labels collected or test sealed.
- T-003B requires scoped R1/R2/R3 PASS, conditional Silver R4 and automation R5 PASS; see state/BLOCKERS.md. Do not advance to T-004 from design completion.

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-004.
