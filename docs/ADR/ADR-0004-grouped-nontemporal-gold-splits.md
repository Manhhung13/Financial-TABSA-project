# ADR-0004: Frozen grouped Gold splits without publication-date requirement
Status: accepted (2026-10-31), supersedes ADR-0003 for the Vietnamese NLP Gold benchmark.

## Context
Vietnamese financial articles may lack reliable publication dates. The project's primary supervised/evaluation goal is target-aspect sentiment on Vietnamese financial news, not chronological market forecasting. Requiring publication dates would unnecessarily block a valid NLP Gold pilot.

## Decision
1. **No timestamp prerequisite:** `published_at` and `first_seen_at` may be `null`. Never invent timestamps or infer them from row order, document ID, the reporting period within an article, or source file order. Missing dates alone do not block T-003.
2. **Group-safe splitting:** verify document identity, exact/near duplicates, translations, republications and same-event links using available source/text/context evidence. Keep all records of one adjudicated document-family/event cluster in the SAME split. Missing event grouping/lineage evidence still requires review; a text hash is not proof that separate articles describe different events.
3. **Split groups, never individual rows:** assign each verified article/event group to train/validation/test **before** expanding into company-aspect rows. A deterministic seeded group allocation (for example, seed=42; configurable 70/15/15 allocation for a sufficiently large dataset) is allowed. Prefer group-aware distribution balancing when feasible; record class, target, aspect and independent-group distributions. Do not use test labels to tune splits or models.
4. **Freeze and protect test:** persist dataset/version, seed, policy version, membership, group evidence and hashes in a split manifest. Seal the test partition, keep it inaccessible during tuning, and use the same frozen test for all model ablations.
5. **Prevent cross-source leakage:** inspect exact/near/event overlaps against Silver, DAPT and auxiliary corpora. Exclude or quarantine overlaps with held-out Gold groups before training. Preserve raw rows and human review decisions; never silently delete or re-label.
6. **Source and label gates remain:** T-012 R1 rights PASS for each used source, R2 identity PASS for included targets, R3 grouping PASS for included rows, R4 if Silver supplies candidates, and an appropriate verified R5 runtime for automated execution. Human-verified presence, polarity and evidence are mandatory.

## Acceptance checks
- No group ID crosses train/validation/test; same article's targets/aspects stay together.
- No unresolved duplicate/event links cross splits; issues are reviewed or excluded.
- Dataset version/manifest/seed are reproducible and test membership is immutable.
- `published_at=null` is allowed and no chronological metric/claim is asserted.
- Human adjudication, source rights and all remaining task gates are satisfied.

## Scope limitation
This group-safe non-temporal Gold benchmark estimates NLP performance under a grouped holdout. It **does not** demonstrate out-of-time generalization or causal stock-market forecasting. A separate future online/market-correlation evaluation must independently verify timestamps and use a causal chronological cutoff.
