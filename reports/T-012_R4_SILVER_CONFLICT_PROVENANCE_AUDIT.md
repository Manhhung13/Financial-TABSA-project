# T-012 R4 — Vietnamese Silver Conflict and Provenance Review

**R4 Silver-derived candidate-use gate: BLOCKED.** Audited only local `data/silver/phobert_dataset.csv`, SHA-256 `93edea2c7babc9432a42259a2d0e48e4ac316e53b44e044483f6a87a1ae1081e`. No raw row was changed; no download, install, training or Gold-label access occurred.

## Findings

- **1,630 rows**, 1,433 normalized `(ticker, content)` keys; 182 repeated-text groups with 197 extra rows.
- **13 confirmed overall-label conflict groups**: repeated normalized ticker/text has more than one `label`. They are reproducible label disagreements, not adjudicated ground-truth contradictions because the generation rubric/provenance is unknown.
- **74 score-only disagreement groups** have the same overall label but differing one or more aspect scores. Across all 182 repeated groups, 85 show at least one differing aspect score (including the 13 label-conflict groups).
- **182 exact normalized text duplicate groups** retained in the duplicate ledger; **71** contain fully identical original rows, with 73 extra fully identical records per T-002. No duplicates were removed.
- All five score fields parse as finite numbers in `[-1,1]`; no invalid or out-of-range values were found. Observed label/ID pairs are internally consistent (negative/0: 240; neutral/1: 381; positive/2: 1,009). This verifies only internal encoding consistency, not semantic correctness.
- Zero scores occur frequently: business 502, leadership 1,352, macro 1,433, capital 1,148, ESG 1,566. Zero is not interpreted as neutral or aspect absence. Score-versus-overall-label summaries are provided descriptively in the ledger; no authoritative mapping or expected relationship is documented, so consistency/correctness cannot be certified.

## Provenance and safe use

The local schema contains no source URL, revision, license, LLM model/model revision, prompt/prompt version or generation date. R1 also found no Silver source/license or generation manifest. All those values remain explicitly `null / unknown`; the local file hash is an integrity fingerprint only. Do not treat the observed label-ID pairing as evidence of a documented label codebook.

Safe policy: retain Silver as **Silver only**; never promote labels to Gold or use them as verified human truth. Exclude all Silver labels/scores from supervised training, evaluation, threshold selection and model selection while provenance and semantics are unresolved. Quarantine the 183 row IDs implicated in the 13 label-conflict and 74 score-only groups from any future Silver label reuse pending review. Other rows remain unverified and are not cleared for pseudo-label reuse; their text may be considered only under separately passed R1 rights, R2 identity and R3 grouping gates. Silver may support task planning or a human review queue if those independent rights and identity gates permit it.

## Gate evidence

- **PASS:** source fingerprint matches R1/T-002; all 1,630 rows and schema columns scanned read-only; deterministic row IDs/hashes and conflict evidence emitted; CPU builder and artifact assertions pass.
- **WARN:** 182 repeated-text groups and 74 score-only disagreements need human review; numeric ranges and label-ID pairs are internally coherent but lack semantic validation.
- **BLOCKED:** 13 overall-label conflict groups unresolved; all 1,630 labels/scores remain unverified pseudo-labels; origin, rights, model, prompt/version and generation date are unknown. Silver-derived candidate selection requiring label reuse is not authorized. If Silver is not used, R4 does not gate T-003.

## Artifacts and validation

- `reports/T-012_R4_silver_conflict_ledger.json` — summary, full conflicting rows and score-only disagreement ledger with source row IDs/hashes.
- `reports/T-012_R4_silver_exact_duplicate_ledger.json` — repeated normalized ticker/text groups, duplicate status, labels and scores.
- `reports/T-012_R4_silver_quarantine_queue.json` — 183 implicated row IDs; review-only quarantine, no raw mutation.
- Validation: standard-library CPU audit completed; generated JSON artifacts parsed and assertions verified 1,630 rows, 13 label-conflict groups, 74 score-only groups and a non-empty quarantine queue. A temporary builder was used during this run and removed to keep changes within authorized report/state files.
