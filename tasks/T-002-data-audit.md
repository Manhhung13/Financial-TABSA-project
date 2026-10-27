# T-002: Data Audit
Status: DONE
Owner: data_worker
Depends on: T-001
Context (read ONLY): docs/DATA_CONTRACT.md;docs/sop/SOP-02-data-governance.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Validate four source data inventories and silver CSV, field meanings, labels, duplication, target aliases, provenance and licenses. Implement only needed audit checks.

## Acceptance criteria
Machine-readable audit report plus counts, hashes, sample anomalies, no invented corrected labels.

## Minimum validation
python -m pytest tests/test_data_contract.py -q (if created)

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-003.
