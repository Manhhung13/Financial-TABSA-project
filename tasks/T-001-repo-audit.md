# T-001: Repo Audit
Status: DONE
Owner: scout
Depends on: none
Context (read ONLY): state/CURRENT.md;docs/ENVIRONMENT.md;docs/SOURCE_AUDIT.md
Allowed scope: targeted relevant project files; no broad refactors, no unrelated edits.

## Task statement
Inventory actual files in D:\financial-tabsa; identify existing scripts, data, checkpoints and tests; report report-vs-code gaps. Read-only.

## Acceptance criteria
A bounded file inventory with verified paths and basic commands; no code/data mutation.

## Minimum validation
Get-ChildItem scripts, src, tests -Recurse; git status --short

## Stop conditions
Missing actual source files, unverified label meaning, Gold test exposure, incompatible adapter, or unapproved expensive GPU training. Record in state/BLOCKERS.md.

## Handoff
Update state/HANDOFF.md (<=12 lines) with changed paths/test evidence. Suggested next: T-002.
