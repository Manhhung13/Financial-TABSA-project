# ADR-0001: LLM-ascribed scores are SILVER
Status: accepted for implementation safety.
Context: User confirmed all five scores in `phobert_dataset.csv` were produced automatically by an LLM. Report table incorrectly suggests using them as direct test labels.
Decision: original dataset stays SILVER; manually adjudicated and independently held-out Vietnamese labels constitute Gold. `0.0` is unknown presence/neutral; never auto-convert. Maintain source provenance and separate versions.
Consequences: label review and challenge samples are prerequisites for valid TABSA test; model results cannot be reported until test is verified.
