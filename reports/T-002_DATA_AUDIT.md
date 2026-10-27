# T-002 Dataset Audit — DONE (audit complete; readiness blockers remain)

**Run:** 2026-10-27; Windows PowerShell; CPU-only; read-only dataset scan. The report generator is [T-002_DATA_AUDIT.py](T-002_DATA_AUDIT.py); machine-readable evidence, including every schema and SHA-256, is [T-002_DATA_AUDIT.json](T-002_DATA_AUDIT.json).

## Access and integrity

Project access and PowerShell command execution succeeded. The system Python 3.13 ran the scan; `.venv\Scripts\python.exe` is unusable because its configured Python 3.11 executable is absent. All seven datasets exist, have expected columns, and have no blank required fields. The six raw files match their manifest SHA-256 values. The 1,630-row Silver file has no corresponding download-manifest record. Manifest records source URLs/revisions/hashes but no license metadata.

| Dataset | Rows | Exact duplicate text rows | Labels / classes | Provenance |
|---|---:|---:|---|---|
| Vietnamese company-tagged | 10,400 | 347 | 10,400 company tags; noisy identity tags, not sentiment | Manifest hash match |
| Vietnamese general sentiment train | 2,953 | 1 | codes 1: 1,481; 2: 853; 0: 619 | Manifest hash match |
| Vietnamese general sentiment validation | 369 | 0 | codes 1: 187; 2: 95; 0: 87 | Manifest hash match |
| Vietnamese general sentiment test | 370 | 0 | codes 1: 188; 2: 99; 0: 83 | Manifest hash match |
| English SEntFiN | 10,753 headlines; 14,371 entity labels parsed | 67 | neutral: 5,507; positive: 5,060; negative: 3,804; 13 parse errors | Manifest hash match |
| Thai financial aspects | 12,258 | 1,801 | 16 aspects; neutral: 5,407; positive: 4,858; negative: 1,993 | Manifest hash match |
| Vietnamese LLM Silver | 1,630 | 197 | overall positive: 1,009; neutral: 381; negative: 240; 29 tickers | No manifest entry |

Exact-text duplicates are counted within each dataset; these do not imply split leakage. SEntFiN uses entity sentiment and is not aspect sentiment. The Vietnamese general sentiment codes 0/1/2 remain unmapped. Thai labels have 16 raw aspect categories; mapping them to five project aspects needs manual review. Silver scores parse as numeric in [-1,1], but a zero score does not establish neutral sentiment or aspect absence. The existing processed audit additionally reports 13 conflicting Silver ticker/text groups; exact cross-source normalized overlap was zero for the sources it compared, but no near-duplicate/event/translation clearance is established.

## Readiness and blockers

- **Stage A: BLOCKED.** DAPT text exists, but decontamination against a sealed Gold test and event/near-duplicate review cannot be demonstrated.
- **Stage B: PARTIAL.** SEntFiN entity labels exist; task/head compatibility, lineage grouping, and approved split protocol remain to be resolved.
- **Stage C: PARTIAL.** Thai aspect/sentiment data exists; taxonomy mapping and row granularity require review.
- **Stage D: BLOCKED.** `data/gold/` contains no files; there is no verified Vietnamese Gold train/validation/test corpus.
- No dataset files were modified; no download, dependency installation, GPU operation, training, or T-003 work was performed.

## Target alias audit

Tag parsing followed the inspected source schemas: VI company `Label` + `Content`; Silver `ticker` + `content`; SEntFiN `Decisions` (Python-literal entity-to-sentiment dictionary) + `Title`; Thai `firm` + `paragraph`. Normalization applies Unicode NFKC, whitespace trim/collapse and uppercase only. Punctuation and token boundaries are preserved; no source tags were rewritten. The project contains no independent, authoritative ticker/company master or verified alias table. Therefore, every distinct normalized tag remains an **unresolved mapping**; cross-dataset string overlap is corroboration of strings only, not identity verification.

| Source | Rows / parsed target values | Distinct raw → normalized tags | Normalization collisions | Heuristic review findings |
|---|---:|---:|---:|---|
| VI company `Label` | 10,400 / 10,400 | 938 → 910 | 28 groups; e.g. `FLC`/`flc`, `POW`/`Pow` | 40 rows with acronym ambiguity (`CEO`, `EPS`, `MOU`, `NAV`, `NIM`, `ROA`); 2 rows with nonstandard `E&C`/`N.Q`; 194 rows where the tag is absent verbatim from its associated content. All are warnings, not confirmed mismatch findings. |
| VI Silver `ticker` | 1,630 / 1,630 | 29 → 29 | 0 | 872 rows where the ticker is absent verbatim from content; context heuristic only. All 29 normalized tags also occur in VI company tags, but neither source is an authoritative identity reference. |
| English SEntFiN entity keys | 10,753 / 14,371 parsed | 4,262 → 3,987 | 272 case/spacing/Unicode groups | 13 `Decisions` parse-error rows; 10 entity-key occurrences contain multi-value delimiters; 108 parsed entity mentions are absent verbatim from the headline. Named targets are entities, not assumed to be tickers. |
| Thai `firm` | 12,258 / 12,258 | 50 → 50 | 0 | 286 rows use `CPI` (ambiguous acronym); 7,498 rows have a firm string outside the unverified three-character ticker heuristic; 12,030 firm values are absent verbatim from Thai paragraph text. These checks do not establish errors. |

No empty or confirmed syntactically invalid tags were found in VI company, Silver or Thai firm fields. No confirmed ticker/company mismatch was established because no trusted reference exists. `E&C`, `N.Q`, acronym-like tags, nonstandard lengths, and context-absent tags are `needs_review` heuristic candidates; the latter can be legitimate when an article uses a company name rather than a ticker. In SEntFiN, representative delimiter cases include `ABB, BHEL` and `BSE, NSE`, which need source-level entity interpretation. Representative evidence and per-tag frequency tables are in [T-002_TARGET_ALIAS_AUDIT.json](T-002_TARGET_ALIAS_AUDIT.json); the reproducible read-only scanner is [T-002_TARGET_ALIAS_AUDIT.py](T-002_TARGET_ALIAS_AUDIT.py).

This closes the T-002 **audit coverage** gap for target aliases. It does not resolve any alias, validate any ticker/company identity, or change the Stage A–D readiness gates above.

## Verification note

The scan uses Python's standard-library CSV parser and computes file hashes without changing source data. No pytest command was run: this audit required no test implementation, and the project virtual environment cannot start. The report records schema, counts, duplicates, label checks, and manifest comparisons in JSON. License evidence is absent from the manifest; obtain/record it before any use requiring confirmed licensing.
