# ADR-0002: Separate classification heads per task
Status: accepted architecture hypothesis (must be tested).
Context: MLM, entity sentiment, Thai aspect+sentiment and Vietnamese TABSA have incompatible output shapes and supervision semantics.
Decision: share/adapt XLM-R encoder across stages; initialize appropriate head per stage, retain stage-specific heads only for stage-specific evaluation, verify adapter transfer explicitly before continuing.
Consequences: no blind checkpoint load and no assumed portability of MLM LoRA to classifier. Keep manifest of transferred weights and tested paths.
