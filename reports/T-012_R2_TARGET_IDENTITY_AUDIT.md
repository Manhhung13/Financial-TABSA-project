# T-012 R2 — Verified Target Identity and Alias Master

**R2 execution: PASS for prioritized Silver target identities; WARN overall for unresolved VI company tags.** The target identity evidence gate is PASS for the 29 ticker candidates in Vietnamese Silver (29/29 identities, 1,630/1,630 rows represented). The overall R2 readiness gate is WARN because selected high-risk VI company tags remain unverified and must not be used as verified targets. R1 source-use restrictions remain independent: these identity results do not clear Silver or VI company data rights for annotation use.

## Scope and method

Read the T-002 alias audit aggregates, R1 provenance/use restrictions and actual source schemas. In Silver, the 29 distinct `Ticker` values were treated as candidates only; their frequency was used to prioritize coverage, never as identity evidence. A code/name pairing was accepted only where an exchange-hosted issuer disclosure, regulator filing or HOSE-hosted listed-company report stated it explicitly. The 25 identities not handled by individual disclosure records are explicit rows in HOSE's 2025 Vietnam Listed Company Corporate Governance Assessment report. The remaining four have direct issuer/regulator disclosures hosted by HOSE. No source rows were changed and no subsidiary, parent or brand aliases were propagated.

## Coverage

| Scope | Coverage | Status |
|---|---:|---|
| Silver ticker identities | 29/29 verified against official code/name evidence | PASS as of cited reference |
| Silver rows represented by those tickers | 1,630/1,630 | PASS for identity coverage only |
| Silver ticker tags still unresolved | 0/29 | — |
| Selected high-risk VI tags | 0/8 issuer mappings verified; 8/8 queued | WARN |
| Selected VI tag occurrences | 42 across 8 tags | WARN; no mappings/corrections assigned |
| Full VI company tag inventory | 910 normalized candidates | Not attempted; outside bounded priority scope |

Top Silver priorities by row frequency were HPG (215), MWG (210), VNM (123), MSN (122), VIC (121), FPT (91), VJC (91), PLX (75), GAS (74), VHM (65), SAB (62), BCM (52), and the remaining 16 candidates. Full frequency ranking is in the machine-readable review queue. The dataset tag itself is not evidence; each master record cites the independent official pairing.

The selected VI warning queue covers `CEO` (32), `NAV` (3), `ROA` (2), `EPS` (1), `MOU` (1), `NIM` (1), `E&C` (1), and `N.Q` (1), totaling 42 selected occurrences. T-002 separately counted 40 occurrences across six financial-term/role acronym warnings and two nonstandard-format warnings. These are heuristic warnings, not confirmed errors. For example, `CEO` can be an issuer ticker and an executive-role term; its occurrence in this dataset cannot be assigned to an issuer solely from that string. No tags were silently fixed.

## Canonical artifacts and validation

- [Issuer/alias master](T-012_R2_issuer_alias_master.json): version 1.0.0; 29 evidence-backed ticker-to-issuer records; reference date and temporal limits recorded; entity relationships are not inferred.
- [Review queue](T-012_R2_review_queue.json): all 29 Silver tickers ranked by frequency and the selected 8 VI warning tags with raw tag, frequency, status and reason. It explicitly records that other target-bearing dataset identity tasks are out of scope here.
- [Read-only validator](../tools/validate_t012_r2_master.py): checks required identity/evidence fields, duplicate verified codes, code/alias consistency, review status and temporal caveat.
- [Artifact builder](../tools/build_t012_r2_artifacts.py): reproducibly derives the queue frequencies from T-002's aggregate audit JSON and writes the curated evidence-backed identity records. It refuses an unexpected Silver ticker set.

Validator result: **PASS**, 29 records, no missing evidence fields or duplicate codes. Ticker frequencies are reproduced from `reports/T-002_TARGET_ALIAS_AUDIT.json`; legal names and citations are populated only from the cited official records below.

## Evidence references

- HOSE-hosted [2025 listed-company assessment report](https://staticfile.hsx.vn/Uploads/UploadDocuments/2421948/VLCA%202025%20-%20Corporate%20Governance%20Assessment%20Report%20Vietnam%202025%20-%20EN.pdf) explicitly pairs the 25 other ticker codes with issuer names in the HOSE/HNX listed-company tables. *(The master stores the specific reference title and URL.)*
- BCM: [Becamex issuer disclosure hosted by HOSE](https://staticfile.hsx.vn/Uploads/UploadDocuments/2438855/20260212%20-%20BCM%20-%20BECAMEX%20HAS%20FULFILLED%20ITS%20TAX%20OBLIGATIONS.pdf), issuer name and Stock Code: BCM.
- BID: [State Securities Commission filing hosted by HOSE](https://staticfile.hsx.vn/Uploads/UploadDocuments/2484326/20260729%20-%20BID%20-%20Reporting%20materials%20on%20the%20result%20of%20the%20share%20issuance%20for%20capital%20increase%20from%20owners%E2%80%99%20equity.pdf), bank legal name, code BID and HOSE listing.
- GAS: [PV GAS issuer disclosure hosted by HOSE](https://staticfile.hsx.vn/Uploads/UploadDocuments/2464363/20260522%20-%20GAS%20-%20CBTT%20Nghi%20quyet%2046%20NQ%20KVN.pdf), issuer legal name and Security symbol: GAS.
- GVR: [Vietnam Rubber Group issuer disclosure hosted by HOSE](https://staticfile.hsx.vn/Uploads/UploadDocuments/2377241/20250527%20-%20GVR%20-%20CBTT%20Tai%20lieu%20hop%20DHDCD%20thuong%20nien%202025%20%28viet%2Banh%29.pdf), company name and Stock code: GVR.

## Gate decisions and remaining blockers

- **R2 subtask execution:** PASS. The bounded Silver priority target set has a versioned master, cited references, review statuses and a passing evidence validator. The high-risk VI candidates are separately surfaced with `needs_review`; no mappings were invented.
- **Gold Pilot R2 target gate:** PASS only for use of these 29 exact Silver ticker identities as targets, subject to source rights and other gates. Selected VI company warning tags are excluded until independently verified. R1 still blocks Silver and warns on VI-company source rights, so this does not authorize their annotation use.
- **Overall identity readiness:** WARN. The other 902 normalized VI company tags were not verified; 28 normalization collisions in the source audit remain a separate alias review concern. SEntFiN and Thai target identities were not expanded in this bounded R2 run.
- **No training-data gate is cleared by ticker identity alone.** R1 licensing, R3 grouping and, if Silver is considered, R4 remain separate. Stage B/C/D and Stage A gates are unchanged.

No R3-R6 or T-003 work was started. Recommended next task is R3 duplicate and event grouping, if explicitly authorized; do not proceed with T-003B until its independent source-rights, target, and grouping gates pass.
