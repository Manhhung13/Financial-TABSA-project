# Project brief / research charter

## Goal
Build an auditable, reproducible Vietnamese financial news classifier conditioned on a target company and one of five business aspects. Inputs: article or target-relevant context, ticker, aspect. Outputs: aspect presence; sentiment NEG/NEU/POS only if present; optional evidence span and confidence with provenance.

## In-scope
- Dataset intake and provenance for Vietnamese (DAPT and Silver), English SEntFiN entity sentiment, Thai financial aspect/sentiment, human-verified Vietnamese Gold.
- Baseline XLM-R, Stage A (MLM), B (entity), C (Thai) and D (Vietnamese target-aspect).
- Dataset leakage checks, ablations, offline evaluation, optional inference API integration after model validation.

## Out-of-scope for initial MVP
- Guaranteeing profitable trading strategies; automatic sentiment labels from future prices; full production ML platform; retraining all historical news; full unbounded LLM agent chain; SOTA claims without same-test comparison.

## Success metrics (not promised results)
Presence F1, conditional sentiment macro-F1, joint tuple F1 and per-aspect breakdown on human-reviewed held-out Vietnamese news. Report variance/seeds, dataset sizes and failures; compare against direct Gold baseline.

## Constraints
Windows PowerShell, Python directly on Windows, RTX 4050 laptop 6GB VRAM, RAM 16GB, PyTorch 2.6.0+cu124 with BF16 available, Transformers 4.56.1, PEFT 0.17.1, Accelerate 1.10.1 observed in user session. Every new environment must be re-verified.

## Source authority
Source: supplied `Bao_cao_phuong_phap_de_xuat_bai_toan(3).docx` (5 pages). Report is a research proposal, NOT evidence that any stage was trained. Proposed corrections are explicitly recorded in `SOURCE_AUDIT.md`.
