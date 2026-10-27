# Master execution plan (proposal - not progress log)

North star: XLM-R target-company/aspect sentiment on verified Vietnamese Gold, with interpretable ablations of A/B/C adaptation.

## Phase order / hard gates
0. Repo reconnaissance, data contracts and sealed Gold split -> required for credible evaluation.
1. E0 direct Gold-only XLM-R baseline -> independent comparison anchor.
2. Stage A Vietnamese DAPT/MLM -> verify adapter portability and MLM val loss -> E1 A->Gold.
3. Stage B SEntFiN EN entity sentiment -> E2 B->Gold and E4 A+B->Gold.
4. Stage C Thai financial aspect/sentiment -> E3 C->Gold and E5 A+B+C->Gold.
5. Stage D Vietnamese Gold TABSA -> end-to-end final head, evidence and per-aspect metrics.
6. E6 optional Silver pretraining if no leakage; review and optionally serve model.

## Must-have work packages (see tasks index)
T-001 repo audit -> T-002 source data audit -> T-003 Gold verified split -> T-004 E0 baseline -> T-005 Stage A -> T-006 Stage B -> T-007 Stage C -> T-008 Stage D -> T-009 ablations -> T-010 inference -> T-011 final academic documentation.

## Gate rules
- Never let automated Silver become Gold test.
- Never use val/test in any pretraining or weak-label curation that would bias benchmark.
- Move past Stage B/C only when loading the inherited encoder/adapter is tested and dataset labels match head shapes.
- Full GPU training runs require explicit go/no-go after smoke on 6GB VRAM.

## Milestones are criteria, not promises
M0 controlled data + test; M1 baseline; M2 validated A/B/C paths; M3 Gold final results; M4 reproducible demo and paper-ready tables.
