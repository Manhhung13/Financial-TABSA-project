# Vietnamese Financial TABSA - draft Gold annotation guide

## Unit
Each row asks about ONE company target and ONE financial aspect, based on the **original content**.
Use `article_pool_to_verify.csv` to read the source text. `ticker_candidate` may be wrong; verify identity before giving a label.

## Allowed values
- `aspect_present`: `yes` or `no` only after manual verification.
- `sentiment`: `negative`, `neutral`, `positive` ONLY when `aspect_present=yes`.
- `annotation_status`: `verified`, `needs_review` or `pending`.
- `evidence`: exact fragment that justifies the label, when present.
- For `aspect_present=no`, leave sentiment and evidence blank (not `neutral`).
- When target is incorrect, translation ambiguous, content mixed or evidence absent, use `needs_review` and explain in `notes`.

## The five aspect categories
1. `business_financials`: reported financial performance, orders, operating cash flow.
2. `leadership_insider`: executives, appointments, management changes, insider transactions.
3. `macro_policy`: macro conditions or policies with an explained relationship to the target company.
4. `capital_structure`: capital increase, share issuance, borrowing, bonds, dividend/capital actions.
5. `legal_esg`: legal/regulatory risk, disclosure enforcement, governance, environment and ESG.

## Labeling principles
- Judge sentiment FOR THE TARGET and THE ASPECT, not the overall headline or sector.
- Distinguish actual results from plans, rumors and expectations.
- Do not infer stock-price direction from sentiment labels.
- `neutral`: related information exists but no clear positive/negative polarity according to the rubric.
- `no`: aspect absent, NOT the same as neutral.
- If positive and negative effects coexist within one target-aspect, mark `needs_review`, consider separating evidence units; do not guess.
- LLM score=0 is NOT proof of neutral or absent.
- Human Gold labels must not copy/accept LLM tags without checking the source.

## Quality
- Do an initial 50-100 article-target pilot.
- Prefer two independent annotators for at least a subset; adjudicate disagreement.
- Protect validation/test from near-duplicates and translations in training or DAPT.
- Preserve timestamps/source URLs where available; timestamps are optional and must never be invented.
- For the Vietnamese NLP Gold benchmark, divide **verified article/document-family/event groups**, not individual aspect rows, into deterministic train/val/test splits (ADR-0004). Missing publication dates alone do not block the split. Unresolved event/near-duplicate links require review or exclusion.

## File workflow
- `article_pool_to_verify.csv` holds context and metadata for manual review.
- `gold_annotation_template.csv` holds five **blank** annotation rows per target/article unit.
- No script in this starter kit marks any row `verified` automatically.
- Human adjudication and train/dev/test splitting must occur before supervised training.
