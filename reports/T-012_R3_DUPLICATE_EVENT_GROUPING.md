# T-012 R3 — Duplicate, Lineage and Event Grouping

**Gate: WARN; T-003B grouping gate BLOCKED.** Read-only CPU audit of the seven R1-authorized local data files, bound to their SHA-256 hashes. No raw rows, labels, checkpoints, downloads or Gold-test labels were edited or used. Gold decontamination is deferred until a Gold test is sealed.

## Coverage and results

| Dataset | Rows scanned | T-002 exact duplicate rows beyond first | Source/article ID | Date |
|---|---:|---:|---|---|
| VI_COMPANY | 10,400 | 347 | absent | absent |
| VI_SENT_TRAIN | 2,953 | 1 | absent | absent |
| VI_SENT_VAL | 369 | 0 | absent | absent |
| VI_SENT_TEST | 370 | 0 | absent | absent |
| EN_SENTFIN | 10,753 | 67 | S No. present; uniqueness/lineage meaning not verified | absent |
| TH_ASPECT | 12,258 | 1,801 | absent | `year` field present |
| VI_SILVER | 1,630 | 197 | absent | absent |
| **Total** | **38,733** | **2,413** | — | — |

Reproducible builder: `tools/build_t012_r3_grouping.py`. It produced deterministic per-row document IDs and source row hashes, raw-text SHA-256 and normalized-text SHA-256. Duplicate ledger contains **1,817 groups** (raw exact and normalized collisions within source); no exact identical text was found across different datasets under the implemented scan. Normalization is NFKC, casefold, punctuation removal and whitespace collapse. It is intentionally conservative for candidate generation but can conflate punctuation-bearing financial text, so normalized matches are review-only. Repeated aspect/company rows preserve their individual document and row IDs.

Near-duplicate candidate queue: **1,604 pairs**, found using shared word-token inverted indexes, capped postings (80), a 15% length band and token Jaccard >=0.88. **707,720 candidate pairs** were scored. This is a CPU-efficient screening heuristic, not a complete recall guarantee; short texts (<80 characters), translation pairs, paraphrases and rare-token candidates may be missed. Boilerplate or common disclosure language may produce false matches. No candidate was merged.

The event queue includes **38,733 rows** as unresolved lineage records; this is not a set of same-event pairs. Only TH_ASPECT has a usable date-like year field in the scanned schemas, and only EN_SENTFIN exposes a source serial. Dates, source IDs, URLs, language/translation references and publication lineage are otherwise absent. Serial order and equal company/ticker are not event evidence. Event IDs remain null pending human adjudication.

## Grouping and split policy

1. Preserve every source row and its raw text/label; never auto-delete or merge. Keep each company/target and aspect annotation attached to its source row. Thai multiple aspect labels remain distinct.
2. Create a document group only after review confirms same original article, translation, or republication from URL/ID, text and source evidence. Create an event group only with corroborating context and date/entity evidence; company identity alone is insufficient.
3. Link translations/republications to the same document-family group when justified; link separate articles about the same event only with evidence. Record reviewer, decision, evidence fields, confidence and policy version. Conflicts remain unresolved.
4. Freeze document/event group IDs before target/aspect expansion. Assign whole groups to chronological train/validation/test partitions; no group may cross splits. Keep all targets/aspects for one article in its assigned split.
5. Seal Gold test before any adaptation-corpus decontamination. After sealing, compare candidate corpora against test document/event groups under a separately audited procedure; do not inspect Gold test labels for tuning or selection.
6. Existing VI sentiment train/val/test assignments are recorded as source metadata and must not be collapsed. Their code semantics remain unknown under R1. No project Gold split exists, so no partition was assigned in R3.

## Cross-source and within-source leakage risks

- **WARN:** 2,413 extra exact-text rows documented by T-002 across sources; they represent duplicate text, not verified duplicate documents or leakage. Duplicate rows remain intact.
- **WARN:** near-duplicate screening found review pairs but cannot establish same article/event; all **1,604** require human adjudication.
- **BLOCKED:** 38,733 rows lack verified event grouping; 38,733 rows are explicitly present in the unresolved lineage queue (some have partial metadata). No split-ready group manifest can be produced.
- **BLOCKED:** there are no Gold rows or sealed Gold test; cross-source Gold contamination cannot yet be assessed. Keep Gold-test decontamination deferred.
- **BLOCKED:** source rights remain unresolved/blocked per R1 for annotation use. R3 grouping evidence does not clear source rights or identity gates.
- **WARN:** within-source VI_COMPANY and Silver duplicates can duplicate article content under multiple noisy target tags. Retain those tags/annotations independently pending identity and event review. VI_SENT source partitions remain explicit. Thai repeated paragraphs may carry multiple distinct aspect rows; retain all labels.

## PASS/WARN/BLOCKED evidence

- **PASS:** all seven expected R1-authorized files scanned; source file hashes match the R1/T-002 local fingerprints; deterministic IDs and raw/normalized hashes emitted for all 38,733 rows; no raw mutation; CPU-only validation completed.
- **WARN:** exact duplicate counts and 1,604 near-text candidates are reproducible, but text equivalence does not establish article or event identity. Metadata coverage is sparse.
- **BLOCKED:** no adjudicated lineage, no frozen group split manifest, and no Gold-test decontamination. T-003B and Stage A grouping gates remain blocked; no R4-R6 or T-003 was executed.

## Artifacts

- `reports/T-012_R3_grouping_ledger.json` — source row, stable IDs, file/raw/normalized hashes, available target/aspect/date/ID values.
- `reports/T-012_R3_exact_duplicate_groups.json` — exact raw/normalized duplicate groups, within and across source.
- `reports/T-012_R3_near_duplicate_review_queue.json` — reviewable candidate pairs and similarity evidence.
- `reports/T-012_R3_event_review_queue.json` — row-level unresolved lineage and missing metadata.
- `tools/build_t012_r3_grouping.py` — deterministic standard-library CPU builder.
