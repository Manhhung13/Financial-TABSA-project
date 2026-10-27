# System architecture / interfaces

Pipeline: source ingestion -> immutable raw article -> normalization/dedup -> target linking -> context extraction -> dataset annotation -> train+val/test -> artifact registry -> inference service -> dashboard.

Proposed training modules (verify actual repo before creating or moving code):
- `src/data/`: downloads, schema validation, provenance, dedup and grouped splits.
- `src/models/`: XLM-R pair encoder, LoRA loading, stage-specific heads.
- `src/training/`: stage A/B/C/D runners and transfer adapters.
- `src/evaluation/`: metrics, slice evaluation, leakage checks and report generation.
- `src/serving/`: optional FastAPI inference, only after model contract is frozen.
- `tests/`: pure validation tests + tiny synthetic training smoke tests.

Interfaces to stabilize before implementation:
1. Dataset manifest (`dataset_id`, source URL, hash, revision, license, split policy).
2. Gold schema (`docs/DATA_CONTRACT.md`).
3. Experiment manifest (`run_id`, config hash, code commit, data version, parent checkpoint, metrics).
4. Inference request (`context`, `ticker`, `aspect`), response (`presence`, `sentiment|null`, `evidence|null`, `model_version`).
5. Checkpoint manifest (base model ID/revision, adapter checkpoint, head shapes, label2id, max_length, tokenizer ID).

Do not create a data warehouse, cloud infrastructure, crawler rewrite or service orchestration without a separate accepted task.
