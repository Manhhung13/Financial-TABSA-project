# T-012 R1 — Provenance and Label Semantics

**R1 audit acceptance: PASS.** Local provenance, hashes, available source-license claims and label documentation were reviewed; the two machine-readable ledgers record the evidence and remaining unknowns. **Data-use readiness is not PASS:** unresolved rights block the affected sources from T-003B. This review did not alter datasets or label mappings.

## Provenance and use gates

All six raw files listed in `data/raw/download_manifest.json` have local SHA-256 values matching the manifest. Hugging Face sources use recorded immutable commit hashes. SEntFiN and Thai entries name mutable `main` branches, not commit revisions. `phobert_dataset.csv` has a local SHA-256 fingerprint but no manifest source, URL, revision, expected hash or license entry.

| Dataset | Source/revision/hash evidence | License evidence and permitted-use status | R1 source status |
|---|---|---|---|
| VI company-tagged | HF repo; pinned commit; local hash matches | Current HF metadata declares MIT. Dataset card does not establish how that declaration applies to underlying publisher articles at the pinned revision. Intended use remains unresolved. | **WARN** |
| VI general sentiment (train/val/test) | HF repo; pinned commit; all three local hashes match | Source page has no dataset card and no license field was found. Use is **UNKNOWN; not permission**. | **BLOCKED** |
| English SEntFiN | GitHub `main`; local hash matches recorded manifest hash; no immutable revision recorded | Repository has an MIT `LICENSE`; available docs do not separately establish rights for the headline dataset. Dataset use remains unresolved. | **BLOCKED** |
| Thai 56-1 aspects | GitHub `main`; local hash matches recorded manifest hash; no immutable revision recorded | Repository README declares CC BY 4.0. Data-specific scope and coverage of underlying filings are not separately established; preserve attribution and keep intended use **WARN** pending confirmation. | **WARN** |
| Vietnamese Silver | Local file only; computed hash is a fingerprint, with no source hash for comparison | No source/license or generation manifest found. Model, prompt/version and generation date are UNKNOWN. Use is **UNKNOWN; not permission**. | **BLOCKED** |

The source pages provide license evidence, not a legal determination of rights in embedded third-party news or filings. For R1’s T-003B gate, a source needs explicit rights evidence for the intended use; WARN/BLOCKED sources are not cleared for annotation-data execution.

## Label semantics

- **VI general sentiment:** the source page exposes `sentiment` as integers 0–2 and says “No dataset card yet”; no codebook was found. Codes **0, 1 and 2 remain UNKNOWN**. Do not infer a polarity mapping from examples, distributions or another model card, and do not use these labels for supervised training until an authoritative codebook is recorded.
- **VI company tags:** `Label` is a noisy company-tag candidate, not a sentiment label. Entity identity remains subject to R2.
- **SEntFiN:** `Decisions` maps entity strings to negative/neutral/positive entity sentiment. This is not aspect-conditioned sentiment; 13 malformed rows remain for R6-B.
- **Thai:** source documentation defines 16 aspects and negative/neutral/positive polarity, and says a text can have multiple aspects. Mapping to the project's five aspects and row granularity remain R6-C work.
- **Silver:** observed overall label strings are positive/neutral/negative, but the exact LLM prompt, model/version and score rubric are unavailable. Keep Silver unverified; numeric zero does not prove absence or neutral. Never promote it to Gold.

## Evidence files and next gate

- [Provenance ledger](T-012_R1_provenance_ledger.json) contains per-file source, revision, byte count, actual hash, manifest comparison, license evidence and use status.
- [Label-semantics ledger](T-012_R1_label_semantics_ledger.json) records code meanings, distributions, unknowns and reuse policy.
- Vietnamese source page: [finance-sentiment-vietnamese](https://huggingface.co/datasets/duong2110/finance-sentiment-vietnamese) (numeric 0–2 only; no dataset card).
- License evidence: [VI company dataset page](https://huggingface.co/datasets/duongnghia222/vietnam_finance_news_company_tagged), [SEntFiN repository license](https://github.com/pyRis/SEntFiN/blob/main/LICENSE), and [Thai source README](https://github.com/nlp-chula/finnlp-sentiment).

**Resolved:** local hashes for all six manifest-listed raw files verified; source field/label meanings documented where the source provides them. **Open:** VI 0/1/2 codebook; VI sentiment license; data-specific license scope for VI company, SEntFiN and Thai; Silver source/license and LLM generation provenance. Do not execute R2–R6 or T-003 under this R1 run.
