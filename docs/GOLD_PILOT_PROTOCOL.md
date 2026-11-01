# Gold Pilot protocol v1 — T-003A design

Status: design complete; no annotation-data execution or Gold seal authorized by this document.
Basis: `DOMAIN_RULES.md`, `DATA_CONTRACT.md`, ADR-0003 and SOP-02. This protocol extends the proposed v1 contract; it does not assert that annotation or sealing software exists.

## Scope and execution gates

The unit is `(context, verified target_company, aspect) -> (aspect_present, sentiment_if_present)`. Labels describe financial information in the supplied text, never predicted returns. Only Vietnamese human-adjudicated, verified records qualify for Gold metrics.

T-003A uses contracts and invented examples only. T-003B stays BLOCKED until an accountable reviewer signs source-specific R1 rights/use PASS, target-specific R2 issuer identity PASS and candidate-specific R3 document/event/translation grouping PASS. Silver candidates additionally need R4 PASS; automated scripts need R5 runtime PASS for the actual environment used. Record evidence paths, hashes, reviewer, date and intended use for every PASS. Missing evidence is BLOCKED, never an implicit PASS. Exclude failed sources/targets; do not waive a gate because another source passed. R6-B/C belong to independent Stage B/C work and do not gate design. Existing queue scripts are not approved by this protocol and must be checked against these gates before execution.

## Record and audit schema

`GOLD_RECORD.schema.json` is a Draft 2020-12 structural schema. `GOLD_SYNTHETIC_EXAMPLES.json` contains invented fixtures only, never candidate data or Gold. Schema conformance alone does not prove rights, identity, human work, grouping or correctness.

| Fields | Meaning / constraint |
|---|---|
| `sample_id`, `article_id`, `event_cluster_id` | Stable IDs; sample ID is `article_id:ticker:aspect`; colon forbidden inside article/ticker IDs. Canonical tuple must be unique within a version. |
| `source`, `source_url`, `source_revision`, `source_row_id`, `license_ref`, `article_sha256` | Trace exact original source and revision, row and rights evidence; hash exact UTF-8 context bytes without normalization. Nullable URL accommodates offline sources with a revision and rights record. |
| `published_at`, `first_seen_at` | Timezone-bearing RFC3339 or null; unknown dates stay null. No fabricated publication dates. |
| `ticker`, `company_name`, `identity_ref`, `target_evidence` | Security code plus canonical issuer identity and approved R2 evidence. Target evidence is an exact context quote resolving that issuer, including a verified alias/coreference where appropriate. |
| `context`, `aspect`, `aspect_present`, `sentiment`, `evidence` | Nonempty fixed context; canonical aspect; boolean presence or unresolved null; positive/negative/neutral or null. Evidence is an exact context quote for present records; empty for absent records. |
| `annotation_status`, `review_reason` | `pending`, `needs_review`, `verified`; nonempty reason for review; verified requires resolved presence and empty reason. Review/pending sentiment is null; reviewer proposals remain in the audit ledger. |
| `annotator_id`, `label_origin`, `guideline_version`, `dataset_version`, `is_synthetic`, `split` | Final accountable reviewer, `human`, frozen rubric/version, explicit fixture flag, and train/val/test/quarantine. Synthetic fixtures always quarantine and cannot enter Gold. |
| `review_ids`, `adjudication_id` | Two distinct immutable independent-review record IDs and a final adjudication record ID for verified records. IDs must resolve in an access-controlled audit ledger; empty/null while pending. |

Ledger design: each review stores sample/context hash, reviewer identity, timestamp, rubric version, independent presence, sentiment proposal, exact evidence and uncertainty reason. A separate assignment table maps review IDs to reviewers; IDs alone do not prove distinct people. Adjudication stores both locked reviews, disagreement type, third reviewer identity, rationale/evidence, outcome and timestamp, including explicit confirmation for agreement cases. Never overwrite earlier reviews or committed labels; issue a new derived version with lineage for corrections.

## Presence and polarity decisions

1. Resolve the target using approved identity evidence. A shared ticker-like token or another firm's result is insufficient. Unresolved identity/context goes to needs_review, never absent.
2. Decide presence separately for each aspect from the supplied context. `false` means a reviewer actively checked and found no target-linked evidence; it never means missing annotation. Then sentiment must be null and evidence empty.
3. If relevant target/aspect evidence exists, presence is true. Assign positive or negative only for explicit or defensibly implied beneficial/adverse financial information in context; neutral means relevant, interpretable information with no clear directional polarity.
4. If evidence is insufficient, contradictory or mixed within one aspect, retain presence=true if relevance is certain, otherwise null; set needs_review and sentiment=null. Never invent a mixed fourth sentiment or force neutral. LLM score zero supplies neither decision.
5. Judge target-specific direction and stated comparator/horizon. A profit decline can be negative despite still-positive earnings; a narrowed loss can be positive. Announced financing, appointments, buybacks and dividends are not automatically positive. Attribute allegations as allegations and preserve uncertainty; negation and conditional language affect meaning.
6. Evidence must justify the decision without outside price knowledge. Keep the fixed context through review. If more context is needed, create a new version, re-review both blind assignments and retain lineage. Do not carve mixed clauses into new samples after seeing labels to force agreement; any context/window policy must be frozen before annotation and retain its group/split.

## Five-aspect rubric

| Aspect | Presence / boundary | Direction examples (conditional on text) | Neutral / review |
|---|---|---|---|
| `business_financials` | Target revenue, earnings, margin, operating performance or cash flow. Financing mechanics belong to capital. | Higher profit or narrower losses: positive; falling revenue/margin: negative. | Standalone financial figure without directional interpretation: neutral; offsetting performance signals: review. |
| `leadership_insider` | Target executives/board appointments, departures, insider transactions. Routine staff news alone is insufficient. | Text-supported beneficial leadership impact: positive; stated management disruption: negative. | Routine appointment or insider trade without stated effect: neutral; uncertain attribution/motivation: review. |
| `macro_policy` | Explicit target linkage to macro/policy exposure or effect. Generic market discussion alone does not establish presence. | Explicit target benefit from a rule: positive; explicit cost/restriction: negative. | Relevant rule exposure with no direction: neutral; unsupported target effect: review (absent only when confidently no link). |
| `capital_structure` | Debt, financing, equity issuance, dividends, buybacks and ownership capital actions. Do not recode operating profits here. | Stated improvement in financing cost: positive; default/dilutive harm stated: negative. | Routine financing announcement without direction: neutral; benefit and dilution together: review. |
| `legal_esg` | Target litigation, penalties, compliance, environmental/social issues and nonroutine governance conduct. Routine executive replacement belongs to leadership. | Explicit clearance/remedy: positive; confirmed fine/violation: negative. | Procedural status without direction: neutral; disputed facts or contradictory effects preventing polarity: review. |

Allow multiple aspects only when each has its own supported relevance and evidence; quotes may overlap if they actually support both decisions. Do not infer all five aspects from an article's global tone.

## Double-blind review and adjudication

Before real review, train two reviewers on synthetic examples and a separately gated calibration pool that can never become sealed test. Freeze guideline v1 and assignment/queue hashes. Calibration may revise the rubric only before production annotation; material later changes require versioning and a fresh blind round.

Assign every article-target packet (all five aspects) to two different reviewers. They cannot see each other's identity, labels, confidence or rationale until both submit and lock. Hide Silver/LLM scores, previous labels, model outputs and intended split. Source/context required for semantic review stays visible; a coordinator independently verifies rights/identity/grouping. Log access and randomize packet order with a recorded seed.

A third qualified reviewer who did not author either review resolves every disagreement in presence, sentiment, evidence sufficiency or entity linkage. The adjudicator inspects locked reviews, source evidence and rubric; records a reasoned outcome rather than majority voting. A third reviewer also confirms agreement cases before verified status. Unresolvable cases remain needs_review/quarantine. Test adjudication is restricted to the annotation/seal team; model developers never receive test labels or label-dependent feedback for tuning. Adjudication results are not a substitute for reporting pre-adjudication agreement.

## Sampling and data-independent queue specification

Proposed initial pilot: at least 100 independently adjudicated event groups, including a disjoint 20-group calibration pool and at least 80 production groups. This is a design target, not a count of available data or statistical-power claim. If eligible supply is smaller, remain pilot-incomplete and report shortfall; never fill from blocked sources.

1. After scoped gates pass, enumerate eligible documents and reviewed exact/near/event/translation lineage; preserve raw rows. Freeze connected leakage groups and the grouping manifest before sampling or pair expansion. A suspected cross-group duplicate blocks the affected groups pending adjudication.
2. Reserve calibration groups first. Select production groups with seed 3003, stable group IDs and documented inclusion probabilities. Stratify by source and verified issuer where feasible; do not require publication periods. Preserve issuer caps and record shortfalls. Never stratify by Silver scores or model labels.
3. Freeze a deterministic non-temporal train/val/test split targeting 60/20/20% of eligible production groups, using seed 3003. Assign complete verified article/document/event/translation groups to one split before expanding aspects. Publication dates are optional and must not affect eligibility or split assignment. Record seed, group membership, actual ratios and manifest hashes. Seal test before model selection.
4. Expand each selected article into verified target packets and exactly five aspect rows only after the split manifest freezes. Retain all candidate lineage; any representative selection is deterministic and documented before labeling. One packet and all its evidence windows inherit one split. Multicompany stories stay in the same leakage group.
5. Queue columns: queue/packet ID, context hash/version, source/revision/rights ref, article/event/document/translation group IDs, verified target/identity ref, guideline version and opaque reviewer assignment tokens. Private coordinator manifest adds gate evidence, split, seed, selection probability and assignment map. Reviewer exports omit split and prior labels and start with blank decisions.

## Validation rules and quality gates

These are proposed conservative pilot acceptance thresholds, frozen before production annotation. They are not measured outcomes. Failures block progression, require a documented remediation/review round and a new version; no post-hoc threshold reduction.

| Gate | Required result |
|---|---|
| Eligibility | 100% of included source/target/group gate evidence resolves to applicable signed PASS; conditional R4/R5 pass. No unresolved identity or rights. |
| Structural | Every record passes the supplied schema with format checking; no duplicate ID/canonical tuple. Require sample ID recomputation and SHA-256 equality against exact context bytes. Evidence and target quotes must be literal context substrings. |
| Review | 100% production rows have two distinct locked human reviews and third-reviewer confirmation/adjudication; every exported Gold row verified. Pending/review rows quarantine and excluded from metrics/training. |
| Pre-adjudication agreement | Report presence raw agreement and Cohen kappa across all resolved paired decisions: >=90% and >=0.80. For jointly-present, resolved sentiment: raw agreement >=85% and kappa >=0.70. Report per-aspect denominators, confusion matrices and unresolved rate; each aspect must meet these thresholds with >=20 comparable decisions for each metric. Zero expected variance/undefined kappa or insufficient support means NOT ASSESSABLE and blocks readiness, not perfect agreement. |
| Coverage and uncertainty | Review five aspects per packet. Report class supports, issuer/source/group distributions and uncertainty on calibration/train/val. Maintain the original minimum coverage thresholds without inspecting or rebalancing sealed test labels. |
| Group integrity | Zero article/document/event/translation overlap across splits and calibration. All target/aspect rows inherit the group split. Publication dates may be null. Verify grouping evidence, hashes and frozen manifest; do not require chronological ordering. |
| Fixture isolation | `is_synthetic=false` for every Gold export; no SYNTHETIC IDs, references or synthetic dataset version. Fixture tests cannot clear eligibility or review gates. |
| Seal and decontamination | Authorized custodian signs immutable version, split/record/ledger/rubric hashes, access policy and validation report. Seal test before Stage A decontamination. Exclude test and validation overlapping groups from all train/adaptation/weak-label pools; a controlled process uses group/text fingerprints without exposing test labels. Require overlap report PASS before any adaptation/training release. |

Presence metrics count unresolved decisions as separately reported missing support, not absence. Sentiment agreement is conditional on both independent reviewers marking present; report presence disagreements separately to avoid hiding them. Compute metrics on production reviews before adjudication within the restricted review team. Only aggregate train/val/calibration diagnostics reach developers; test-specific annotation QA stays with the custodian. Test access is logged, final evaluation uses a locked model/config, and no test-label-derived advice feeds preprocessing, prompting, thresholds or model selection.

Cross-record/audit rules above cannot be enforced by a single-record JSON Schema; their future validator must join the ledger, rights/identity registry and frozen grouping/split manifests. This design does not implement or run that data validator. Structural synthetic validation may use an existing CPU Python plus `jsonschema.Draft202012Validator` with `FormatChecker`; no new dependencies are authorized.

## Current disposition

T-003A deliverables are design artifacts only. T-003 overall acceptance (actual verified Gold, grouping manifest, leakage checks and sealed test) remains unmet. T-003B is blocked by the existing R1/R3, target-scoped R2 and conditional R4/R5 blockers recorded in `state/BLOCKERS.md`. No dataset inspection, candidate sampling, actual labels, training or seal is part of this task.
