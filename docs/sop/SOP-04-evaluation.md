# SOP-04: Model evaluation / research evidence
1. Verify human Gold test status and a frozen non-temporal article/event-group partition with no group overlap; publication dates are optional (ADR-0004).
2. Use identical test samples and task head across E0..E6.
3. Report presence F1; conditional sentiment macro-F1; joint tuple F1, per-aspect scores, multi-company slice; state independent article counts.
4. For finalists, run repeated seeds; show variance and calibration if used.
5. Record mistakes (wrong ticker, missing context, absent-vs-neutral, ambiguous/mixed, class imbalance) with evidence IDs.
6. Only after model frozen, run Gold test once for final results. Separate price-direction predictive validity from NLP scores.
