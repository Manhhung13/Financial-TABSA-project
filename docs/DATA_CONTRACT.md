# Data contracts (version v1 - proposals, not claim of existing code)

## Dataset inventory / permitted use
| ID | Source | Labels | Allowed initial use |
|---|---|---|---|
| VI_TEXT | Vietnam Finance News Company Tagged (~10,400 rows as stated in source) | text, noisy company tag | DAPT text; select candidates; NOT sentiment labels |
| VI_SENT | finance-sentiment-vietnamese (~3,692 rows from earlier audit) | global sentiment 3 classes | OPTIONAL auxiliary general sentiment; do not expand to aspect labels |
| EN_ENTITY | SEntFiN (~10,753 headlines) | company-specific sentiment | Stage B; group by original headline |
| TH_ASPECT | Thai financial disclosures (~16 aspects) | aspect and sentiment (check row granularity) | Stage C; do NOT assume ticker-level labels |
| VI_SILVER | phobert_dataset.csv (1,630 rows, 29 tickers) | LLM-generated overall and 5 scores | SILVER only; annotation sampling; never unverified Gold test |
| VI_GOLD | Manually adjudicated Vietnamese company-aspect annotations | presence, polarity, evidence | stage D train/val/test per frozen partition |

## Canonical Gold record (JSONL or Parquet)
```json
{"sample_id":"articleA:HPG:legal_esg","article_id":"articleA","event_cluster_id":"event42","source":"cafef","source_url":null,"published_at":null,"first_seen_at":null,"ticker":"HPG","company_name":null,"context":"Example context","aspect":"legal_esg","aspect_present":true,"sentiment":"negative","evidence":"Example evidence","annotation_status":"verified","annotator_id":"ann01","label_origin":"human","dataset_version":"gold-v1","split":"train"}
```
Unknown timestamps remain NULL; never fabricate dates. Use `sentiment=null` when absent/needs_review. Only `verified` samples qualify for Gold metrics.

## Mandatory validation
- Required columns, nonempty context/ticker/aspect (when applicable), known aspect keys, known sentiment labels.
- Unique canonical sample IDs; preserve source original rows, hashes, URL, dataset revision and license metadata.
- Dedup exact + near duplicate/event cluster; split by article/event BEFORE expansion into five aspects; remove overlaps with eval/test from all adaptation corpora.
- Any automatic label correction saved as new derived dataset version with provenance, not mutating original.
- No numeric aspect score mapped to label without reviewed schema/rules; 0.0 ambiguous.
- Gold test stays inaccessible for preprocessing/hyperparameter decisions except final locked evaluation.

## Storage layout (proposed)
`data/raw/{vi,en,th}/`, `data/interim/`, `data/silver/`, `data/gold/`, `data/manifests/`, `artifacts/`, `experiments/`.
These folders may differ in existing project; T-001 audits real paths before code changes.
