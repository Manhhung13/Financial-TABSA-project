# SOP-05: Inference service/release
1. Require verified final Gold evaluation, model/version manifest, label mapping and tokenizer compatibility.
2. API returns ticker, aspect, presence, sentiment|null, confidence and evidence/source IDs when available; schema tests mandatory.
3. Smoke case with two entities and opposing sentiments; unknown aspect and empty context return controlled errors.
4. Validate measured latency and VRAM on target Windows laptop; do not present unmeasured claims.
5. Log model version and input hash without exposing private raw documents; enable rollback to prior checkpoint.
6. Never deploy a checkpoint missing required heads or whose adapter transfer is unverified.
