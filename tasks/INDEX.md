# Task index (state of work is in state/CURRENT.md)

| ID | Task | Prerequisite | Owner role | Status |
|---|---|---|---|---|
| T-001 | Repo audit and reconciliation | none | scout | DONE |
| T-002 | Dataset source audit + schemas | T-001 | data_worker | DONE |
| T-012 | Data Readiness (sequenced as T-002.5) | T-002 | data_worker | TODO |
| T-003 | Gold annotation + split seal | T-002 for T-003A design; T-012 R1-R3 PASS for T-003B data execution | data_worker + reviewer | TODO |
| T-004 | E0 XLM-R Gold baseline | T-003 | implementer | TODO |
| T-005 | Stage A DAPT + transfer | T-002,T-003 | implementer + ml_architect | TODO |
| T-006 | Stage B EN entity sentiment | T-002,T-005 (sequential path); T-012 R6-B PASS | implementer | TODO |
| T-007 | Stage C Thai auxiliary | T-002,T-006 (sequential path); T-012 R6-C PASS | implementer | TODO |
| T-008 | Stage D VI final model | T-003,T-004,T-007 (combined path) | implementer | TODO |
| T-009 | Ablation + frozen Gold test | T-004..T-008 | reviewer + ml_architect | TODO |
| T-010 | Inference integration | T-008,T-009 | implementer | TODO |
| T-011 | Academic report and handoff | T-009 | reviewer | TODO |

Task status in this file is an index; only `state/CURRENT.md` and completed evidence determine actual done state. T-012 is parser-safe registration for the proposed T-002.5 readiness gate. T-003A is a design-only subtask label inside `T-003-gold-seal.md`; it is not a standalone parser-visible task ID. T-003B data execution requires the specified T-012 gate evidence. DO NOT mark stages trained merely because prior starter scripts were generated.
