# T-012: Data Readiness (sequenced as T-002.5)
Status: TODO
Owner: data_worker
Depends on: T-002 (DONE)
Context (read ONLY): docs/DATA_CONTRACT.md;docs/sop/SOP-02-data-governance.md;docs/DOMAIN_RULES.md;docs/ADR/ADR-0004-grouped-nontemporal-gold-splits.md
Allowed scope: targeted source metadata and derived audit/review artifacts; no raw data, committed Gold labels, checkpoints, downloads, package installs or training.

## Task statement
Complete six bounded readiness reviews. This task records dataset and model-training gates separately: T-012 may be complete with a Stage-specific gate still WARN/BLOCKED. No T-003 annotation-data execution or model training is authorized by registering this task.

### PASS / WARN / BLOCKED evidence convention
- PASS: the stated gate has reproducible evidence and is safe for its defined use.
- WARN: a documented limitation permits a narrower use; exclusions and scope are explicit.
- BLOCKED: required rights, semantics, identity, grouping, runtime or review evidence is missing. Do not proceed through that gate.

### Six bounded subtasks
1. **R1 — Provenance and label semantics (P0, Gold Pilot):** record source URL/revision/hash, license evidence and permitted use for each proposed annotation source. Resolve Vietnamese general-sentiment codes only from a source codebook; otherwise keep them unknown and prohibit their supervised reuse. Do not use labels to create Gold. A source can support annotation-data execution only when its rights pass; code semantics are required only when those source labels are reused.
2. **R2 — Target identity (P0, Gold Pilot):** define a versioned company/alias master from a trustworthy, cited reference, with raw value, normalized value, alias type, valid-time evidence where available, reference, reviewer, status and rationale. Do not treat VI tags, Silver, frequency or cross-dataset overlap as independent verification. Unresolved targets remain `needs_review` and cannot enter Gold annotation-data execution as verified companies.
3. **R3 — Duplicate and event grouping (P0, Gold Pilot):** preserve source rows and raw hashes; compute separate exact-normalized hashes; generate near-duplicate candidates for human adjudication; record article, event, translation and republication links with evidence and confidence. Never delete or silently merge rows. Define article/event split grouping before pair expansion; publication dates are optional and non-temporal grouped splitting is valid under ADR-0004. Gold-test decontamination is a later gate, after Gold is sealed, and must not use test labels for tuning.
4. **R4 — Silver provenance and conflict review (P1, optional candidate source):** inventory the 13 conflicting ticker/text groups; retain all source rows and conflicting labels/scores; record available prompt/model/version provenance and mark unavailable metadata unknown. Silver remains Silver and cannot become Gold. R4 gates Silver-derived candidate selection only; it does not gate T-003 if Silver is not used.
5. **R5 — Environment (P2, automated checks):** document the broken `.venv` interpreter reference and a no-upgrade recovery plan. Verify an existing supported CPU runtime and reproducibility of lightweight checks. Recreating environments or installing packages requires separate authorization; this subtask does not permit it.
6. **R6 — Independent Stage B/C readiness (P1):** publish separate sub-gates. **R6-B:** quarantine the 13 SEntFiN parse-error rows in a derived artifact with original row, hash and reason; verify entity-level label semantics, headline grouping, rights and head/adapter plan. **R6-C:** human-review Thai row granularity, all 16 aspect meanings and sentiment classes; record explicit mappings or `unmapped`, rights and the correct modeling task. Neither gate is a prerequisite for the Gold Pilot; R6-B gates Stage B training and R6-C gates Stage C training independently.

## Gold Pilot execution gates
- **T-003A (annotation design only):** may proceed after T-002 without T-012 PASS if it uses project contracts/guidelines only and does not inspect or sample source rows. It may define schema, rubric, reviewer protocol and a data-independent queue specification.
- **T-003B (annotation-data execution/seal):** requires R1 source-rights PASS for each included source, R2 target-identity PASS for each included target, and R3 grouping PASS. If Silver is selected as a candidate source, R4 must PASS for that use. Any automated processing additionally requires R5 PASS for that runtime. A blocked source/target is excluded; do not infer a substitute mapping or label.
- These are scoped gates, not a requirement that all R4/R5/R6 results be PASS before T-003A or an otherwise-valid T-003B pilot can proceed.

## Stage readiness gates
- **Stage A:** authorized text-only corpus and hashes; R3 grouping and documented post-seal test decontamination; no unverified supervised labels in MLM data; runtime PASS before automated training.
- **Stage B:** R1 rights/label-use PASS, R6-B PASS, original-headline/event grouping, entity-level evaluation protocol and compatible encoder/head/adapter evidence.
- **Stage C:** R1 rights PASS, R6-C PASS, reviewed taxonomy/granularity and explicit mapping manifest; compatible encoder/head/adapter evidence.
- **Stage D:** verified human Gold per contract; R2 target validity and R3 verified document/event grouping (not publication-time grouping); frozen grouped split manifest and sealed test. Missing timestamps alone do not block the Gold split. Silver is never a substitute.

## Acceptance criteria
- Six subtask outputs each carry PASS/WARN/BLOCKED with source-backed evidence, exclusions and unresolved items; preserve raw values and make no invented corrections/mappings.
- Machine-readable provenance, identity, grouping and conflict ledgers identify source/hash/row and retain review decisions; derived artifacts are versioned and do not overwrite raw or Gold.
- Gold Pilot and Stage A-D gates are separately reported; no task completion status is presented as model-training readiness.
- `T-003A` and `T-003B` boundaries are explicit; T-003B is blocked for any source lacking rights or any target lacking verified identity.
- No downloads, installs, raw-data edits, Gold-test label access, training, or automatic duplicate deletion.

## Minimum validation
python tools/validate_governance.py

## Stop conditions
Unknown source rights, unverified target identity, ambiguous labels, unresolved split/event lineage or unauthorized environment changes. Record evidence and exact blocked gate in `state/BLOCKERS.md`.

## Handoff
Update `state/HANDOFF.md` (<=12 lines) and `state/CURRENT.md`; do not automatically start T-003.
