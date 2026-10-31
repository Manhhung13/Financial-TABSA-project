# SOP-02: Data intake, audit and label provenance
1. Fetch/source revision only with explicit permission; retain raw immutable data + SHA256+URL+license.
2. Validate schema and sample target/label semantics. Tag suspicious company aliases (e.g. ROA/NIM) as unknown, never as ticker truth.
3. Dedup exact and near duplicates. Group by original article, event and original/translation lineage.
4. Split VERIFIED article/document-family/event groups (no date requirement) BEFORE window/target/aspect expansion; record seed and frozen group manifest; seal Gold test before adaptations. Dates remain nullable (ADR-0004).
5. If annotation from LLM, store `label_origin=llm`, prompt/model/version and `annotation_status=unverified`.
6. Map Thai taxonomy only after manual review. Missing aspect annotation != absent; score 0 != neutral.
7. Emit audit summary: counts, missing labels, label imbalance, overlap rates, unverified assumptions and manifest hash.
