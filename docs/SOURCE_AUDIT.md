# Source report audit - provenance vs recommendations

Reference: `docs/reference/source_report.docx`, user-provided report. It has 5 pages, proposes XLM-R stage A(DAPT/MLM) -> B(SEntFiN entity) -> C(Thai aspect/sentiment) -> D(Vietnamese Gold TABSA) in summary (page 2).

## Directly supported by report
- Task input `(context, target_company, aspect)` and outputs `(aspect_present, sentiment_if_present)` (p2).
- Five aspect outputs (context of project) and pair-based context/query encoding (p3).
- Stage A MLM on financial Vietnamese text (p4), Stage B entity-level English supervised fine-tune (p4), Stage C Thai aspect+sentiment (p5).
- The report describes the 1,630 rows/29 tickers LLM-generated labels as data; no validated Gold quality metrics are given (p2).

## Gaps / contradictions that should not be copied into code
1. Report table row says `phobert_dataset.csv` used to test model; labels are LLM-generated, so treat as SILVER unless manually verified and held out.
2. Executive summary mentions Stage D but detailed chapters do not specify complete Stage D protocol.
3. Diagram says Stage C -> FastAPI, omitting Gold fine-tuning D; treat D as required before serving final target-aspect claims.
4. Thai row structure and multi-label vs single-label behavior must be verified against actual release; report says use 16-class head provisionally.
5. No runtime evidence for model performance, memory or checkpoint transfer is present in report.

These corrections are project governance recommendations, not quotations from the source. Preserve original report unchanged for academic traceability.

## T-001 repository audit (2026-10-27)

Verified in `D:\financial-tabsa`:
- Scripts: `scripts/01_gpu_smoke_test.py`, `02_download_datasets.py`, `03_audit_prepare.py`, `04_create_gold_review.py`, `04_quality_gate_pretrain.py`, and `05_train_stage_A_dapt.py`.
- `01_gpu_smoke_test.py` loads XLM-R and runs a CUDA forward pass without training. `05_train_stage_A_dapt.py` implements Vietnamese financial-domain MLM with LoRA and exposes prepare/smoke/train modes; Stage A is not sentiment training.
- `02_download_datasets.py` fetches source data with a manifest; `03_audit_prepare.py` creates separate candidate/preprocessing outputs and overlap summaries; `04_create_gold_review.py` creates blank human-annotation templates; `04_quality_gate_pretrain.py` performs CPU label-quality/leakage candidate checks.
- `src/` and `tests/` contain only `AGENTS.md`. No checkpoint metadata files were found. `data/silver/phobert_dataset.csv` is SILVER, not Gold.
- No Stage B entity-sentiment, Stage C Thai aspect/sentiment, or Stage D Vietnamese Gold TABSA training pipeline is present. Gold annotation templates do not constitute an adjudicated Gold set.

Unverified runtime conditions: installed dependency versions, live CUDA/GPU availability, cached/downloadable XLM-R weights, Stage A input readiness, successful smoke/training execution, and any trained checkpoint. Stage A `--mode smoke` performs five GPU training steps by default; it was not run during this read-only audit.

Recommended next task: T-002. Keep Stage B distinct from Stage A MLM, verify adapter/head compatibility, and add focused tests alongside its implementation. T-002 has not been started.
