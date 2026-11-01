T-003A DONE (design only, 2026-10-27); T-003B BLOCKED; Gold not sealed.
T-003A artifacts: docs/GOLD_PILOT_PROTOCOL.md and docs/GOLD_RECORD.schema.json.
Synthetic-only fixtures: docs/GOLD_SYNTHETIC_EXAMPLES.json (10 examples, never Gold).
Agent reported schema self-check, 10 valid fixtures and 19 invalid-case checks PASS.
ADR-0004 supersedes ADR-0003: publication dates optional for Vietnamese NLP Gold.
Split verified article/document-family/event groups, not dates or individual rows; freeze test.
R1 source rights, R2 article-target identity and R3 event grouping must PASS for included records.
R2 master has 29 validated ticker identities; individual article links remain unverified.
R4 gates Silver candidate reuse; do not automatically promote Silver labels.
Local Python/pandas/pip checks OK; full R5/CUDA not verified; R6 BLK-031 unresolved.
Script 04 generates blank review sheets; provisional text hash is not a verified event group.
Next: check T-003A documents against ADR-0004 and resolve source gates before T-003B.
