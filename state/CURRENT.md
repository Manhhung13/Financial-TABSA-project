# Current verified state
Updated: 2026-11-01 (T-003A design complete; Gold split policy updated)

- T-001 DONE; T-002 DONE.
- T-003A DONE (design only); overall T-003 and Gold seal NOT complete.
- Gold Pilot protocol: docs/GOLD_PILOT_PROTOCOL.md.
- Gold schema: docs/GOLD_RECORD.schema.json.
- Synthetic fixtures: docs/GOLD_SYNTHETIC_EXAMPLES.json (10 invented examples, NOT Gold).
- Agent reported schema self-check, 10 fixtures, and 19 invalid-case checks PASS using Conda Python 3.13.12.
- Owner approved ADR-0004 on 2026-10-31; ADR-0003 superseded for Vietnamese NLP Gold.
- Publication dates are OPTIONAL. Split by verified article/document-family/event groups, NOT by time or individual aspect rows.
- Chronological validation remains necessary for a separate causal stock-market evaluation.
- T-003B BLOCKED: R1 source rights, R2 row-level target identity, and R3 event grouping remain unresolved.
- R2 master validates 29 ticker identities, but individual Vietnamese article-target links are not verified.
- R4 Silver provenance remains BLOCKED; Silver cannot automatically become Gold.
- R5: user reports local Python 3.11.7, pandas 3.1.0 and pip check OK; full runtime/CUDA not validated.
- R6 environment repair remains BLOCKED at BLK-031; requirements manifest conflict is unresolved.
- No real Gold labels, frozen train/validation/test split, or sealed Gold test produced.
- T-003A produced design artifacts only; no training or checkpoint changes.
- Next: preserve T-003A artifacts, validate them against ADR-0004, then resolve R1/R2/R3 before T-003B.
