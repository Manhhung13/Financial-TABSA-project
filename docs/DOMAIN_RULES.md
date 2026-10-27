# Business rules: target-aspect financial sentiment

## Task definition
One record represents (context, target_company, aspect). Presence indicates whether text contains evidence relevant to that company and aspect. Sentiment is defined ONLY when presence=true and evidence is sufficient. Labels are textual financial-information polarity according to annotation policy, NOT actual or predicted future stock returns.

## Canonical five aspects
| Key | Scope | Typical clues | Exclude/route |
|---|---|---|---|
| `business_financials` | Revenue, profit/loss, margin, cash flow, operating results | profit grew, losses narrowed, revenue decline | financing transaction -> capital |
| `leadership_insider` | Appointments/departures of leadership, insider dealings | CEO replaced, insider share trades | ordinary employee news -> examine ESG/context |
| `macro_policy` | Macro or policy events relevant to target company | policy shift, interest-rate rule | generic market news with no supported target effect -> review |
| `capital_structure` | Debt, financing, equity issuance, dividends, ownership capital actions | bonds issued, rights offering, buyback | profit announcements -> business |
| `legal_esg` | Lawsuits, penalties, compliance, environment, relevant governance/social issues | disclosure fine, environmental case | routine leadership change -> leadership |

## Presence / sentiment
- presence=false: No evidence about this aspect for this target in provided context. sentiment=null.
- presence=true, sentiment=neutral: Relevant content exists but annotator judges no clear POS/NEG polarity.
- presence=true, sentiment=positive or negative: Explicit or defensibly implied contextual polarity.
- mixed or contradictory effects in one aspect: mark `needs_review` and/or split evidence according to annotation guideline; do not silently force a label.
- unknown labels: `annotation_status=needs_review`, not neutral.
- The LLM silver score of 0.0 is ambiguous and must NOT generate presence=false or neutral automatically.

## Entity linkage
One article may produce distinct predictions for different firms; targets are not interchangeable. Ticker and alias normalization require validation; terms such as ROA, NIM, MOU are not automatically listed companies. Target markers may help but cannot replace ground-truth entity resolution.

## Evidence and provenance
Store source article/version, target span or verified alias, evidence quote/span, label origin, annotator and guideline version. Do not replace real company names with fabricated Vietnamese tickers in historical datasets.
