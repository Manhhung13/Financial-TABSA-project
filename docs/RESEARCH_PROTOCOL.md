# Research protocol - reproducible claims only

## Primary test
Human-verified Vietnamese Gold target-aspect records grouped by article/event; locked chronological train/validation/test. Retain counts of independent articles and expanded samples. Val for model selection, Gold test for final evaluation only.

## Required metrics
Presence precision/recall/F1; sentiment macro-F1 and per-class F1 on present aspects; end-to-end F1 `(ticker,aspect,sentiment)`, per-aspect slices, multi-company sample slice; confusion matrices, sample counts and uncertainties. Report throughput/VRAM if measured.

## Ablations
E0 direct XLM-R -> Gold; E1 A -> Gold; E2 B -> Gold; E3 C -> Gold; E4 A+B -> Gold; E5 A+B+C -> Gold; E6 carefully filtered Silver + Gold (optional). Compare same backbone/head, same Gold train/val/test; source-stage heads replaced appropriately.

## Data leakage gates
- Split at article/event level before target-aspect expansion.
- Dedup cross-sources (exact and near duplicates) including silver, translated versions and DAPT corpus against Gold validation/test.
- Timestamp-aware restrictions for market forecasting separate from NLP results.
- Never tune prompts, weak label rules, thresholds or hyperparameters based on Gold test.

## Experiment record
For each run: code commit, seed, input manifest/hash, base model revision, stage path, tokenization, optimizer, LR, batch and grad acc, BF16 setting, max length, epoch/steps, val metrics, GPU peak, checkpoints and exception details. Record failures as failures, not results.

## Statistical honesty
Prefer >=3 seeds for finalists; report average and variation. Avoid calling higher MLM accuracy a sentiment win. The separate stock-price experiment must include news-count and market-only baselines and a strictly causal cutoff.
