"""Build derived, source-preserving T-012 R2 identity audit artifacts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports" / "T-002_TARGET_ALIAS_AUDIT.json"
R1 = ROOT / "reports" / "T-012_R1_provenance_ledger.json"
MASTER = ROOT / "reports" / "T-012_R2_issuer_alias_master.json"
QUEUE = ROOT / "reports" / "T-012_R2_review_queue.json"

HOSE_REPORT = {
    "title": "2025 Vietnam Listed Company CG Assessment Report, HOSE listed company table",
    "url": "https://staticfile.hsx.vn/Uploads/UploadDocuments/2421948/VLCA%202025%20-%20Corporate%20Governance%20Assessment%20Report%20Vietnam%20Listed%20Companies%202025%20-%20EN.pdf",
    "date": "2025 (report)",
}
ISSUERS = {
    "ACB": "Asia Commercial Joint Stock Bank",
    "CTG": "Vietnam Joint Stock Commercial Bank For Industry And Trade",
    "FPT": "FPT Corporation",
    "HDB": "Ho Chi Minh City Development Joint Stock Commercial Bank",
    "HPG": "Hoa Phat Group Joint Stock Company",
    "LPB": "Fortune Vietnam Joint Stock Commercial Bank",
    "MBB": "Military Commercial Joint Stock Bank",
    "MSN": "Masan Group Corporation",
    "MWG": "Mobile World Investment Corporation",
    "PLX": "VietNam National Petroleum Group",
    "SAB": "Saigon Beer - Alcohol - Beverage Corporation",
    "SHB": "Saigon Hanoi Commercial Joint Stock Bank",
    "SSB": "Southeast Asia Commercial Joint Stock Bank",
    "SSI": "SSI Securities Corporation",
    "STB": "Saigon Thuong Tin Commercial Joint Stock Bank",
    "TCB": "Vietnam Technological and Commercial Joint Stock Bank",
    "TPB": "Tien Phong Commercial Joint Stock Bank",
    "VCB": "Joint Stock Commercial Bank for Foreign Trade of Vietnam",
    "VHM": "Vinhomes Joint Stock Company",
    "VIB": "Vietnam International Commercial Joint Stock Bank",
    "VIC": "Vingroup Joint Stock Company",
    "VJC": "Vietjet Aviation Joint Stock Company",
    "VNM": "Vietnam Dairy Products Joint Stock Company",
    "VPB": "Vietnam Prosperity Joint Stock Commercial Bank",
    "VRE": "Vincom Retail Joint Stock Company",
}
SPECIAL = {
    "BCM": ("Becamex Investment and Industrial Development Group", "2026-02-12", "https://staticfile.hsx.vn/Uploads/UploadDocuments/2438855/20260212%20-%20BCM%20-%20BECAMEX%20HAS%20FULFILLED%20ITS%20TAX%20OBLIGATIONS.pdf", "Becamex issuer disclosure hosted by HOSE", "Issuer disclosure names Becamex Investment and Industrial Development Group and states Stock Code: BCM."),
    "BID": ("Joint Stock Commercial Bank for Investment and Development of Vietnam", "2026-07-28", "https://staticfile.hsx.vn/Uploads/UploadDocuments/2484326/20260729%20-%20BID%20-%20Reporting%20materials%20on%20the%20result%20of%20the%20share%20issuance%20for%20capital%20increase%20from%20owners%E2%80%99%20equity.pdf", "State Securities Commission filing hosted by HOSE", "SSC filing identifies the bank (Stock Code: BID, listed on HOSE)."),
    "GAS": ("PetroVietnam Gas Joint Stock Corporation", "2026-05-22", "https://staticfile.hsx.vn/Uploads/UploadDocuments/2464363/20260522%20-%20GAS%20-%20CBTT%20Nghi%20quyet%2046%20NQ%20KVN.pdf", "PV GAS issuer disclosure hosted by HOSE", "Issuer disclosure names PetroVietnam Gas Joint Stock Corporation and states Security symbol: GAS."),
    "GVR": ("Vietnam Rubber Group - Joint Stock Company", "2025-05-27", "https://staticfile.hsx.vn/Uploads/UploadDocuments/2377241/20250527%20-%20GVR%20-%20CBTT%20Tai%20lieu%20hop%20DHDCD%20thuong%20nien%202025%20%28viet%2Banh%29.pdf", "Vietnam Rubber Group issuer disclosure hosted by HOSE", "Issuer disclosure states Company name and Stock code: GVR."),
}

audit = json.loads(AUDIT.read_text(encoding="utf-8"))
r1 = json.loads(R1.read_text(encoding="utf-8"))
silver = audit["sources"]["vi_silver"]["raw_tag_frequencies"]
assert set(silver) == set(ISSUERS) | set(SPECIAL), "Silver ticker set changed; review source before regenerating"
silver_hash = next(f["sha256"] for s in r1["sources"] if s["dataset"] == "VI_SILVER_PHOBERT" for f in s["local_files"])
company_hash = next(f["sha256"] for s in r1["sources"] if s["dataset"] == "VI_COMPANY" for f in s["local_files"])

records = []
for code in sorted(silver):
    if code in SPECIAL:
        name, date, url, title, evidence = SPECIAL[code]
        ref = {"title": title, "url": url, "date": date}
        method = "issuer or regulator disclosure hosted by exchange; exact code/name pairing"
    else:
        name = ISSUERS[code]
        ref = HOSE_REPORT
        evidence = f"HOSE listed-company table explicitly pairs {code} with {name}."
        method = "official exchange-hosted report; exact code/name pair"
    records.append({
        "record_id": f"T012-R2-SILVER-{code}", "alias_raw": code, "alias_normalized": code,
        "alias_type": "ticker", "entity_type": "issuer", "legal_name_as_evidenced": name,
        "security_code": code, "exchange": "HOSE", "valid_from": None, "valid_to": None,
        "reference_title": ref["title"], "reference_url": ref["url"], "reference_date": ref["date"],
        "evidence": evidence, "verification_method": method,
        "review_status": "verified_as_of_reference", "reviewer": "Codex audit",
        "reviewed_at": "2026-10-27",
        "rationale": "Explicit official code/name pairing. The cited reference date is evidence; legal validity beyond it is not asserted.",
        "source_dataset": "VI_SILVER_PHOBERT", "source_row_frequency": silver[code],
        "source_file": "data/silver/phobert_dataset.csv", "source_sha256": silver_hash,
    })

master = {
    "task": "T-012 R2", "version": "1.0.0", "created_at": "2026-10-27",
    "scope": "29 Vietnamese Silver ticker candidates and selected high-risk VI company tags; identity verification only, not source-use clearance",
    "normalization_policy": {"unicode": "NFKC", "whitespace": "trim and collapse runs", "case": "uppercase ticker aliases; preserve legal names as cited", "ticker_format": "exact code as explicitly paired in cited official record; no inferred transformations", "relationships": "issuer, parent, subsidiary and brand remain distinct; no relationship inferred"},
    "record_schema": ["record_id", "alias_raw", "alias_normalized", "alias_type", "entity_type", "legal_name_as_evidenced", "security_code", "exchange", "valid_from", "valid_to", "reference_title", "reference_url", "reference_date", "evidence", "verification_method", "review_status", "reviewer", "reviewed_at", "rationale", "source_dataset", "source_row_frequency", "source_file", "source_sha256"],
    "reference_policy": "Only issuer/exchange or regulator disclosure records with an explicit security-code and issuer-name pairing are accepted. Dataset tags and frequency are not identity evidence.",
    "source_files": [{"path": "data/silver/phobert_dataset.csv", "sha256": silver_hash, "rows": 1630, "note": "Local fingerprint from R1; no source manifest, source URL or license. Used only to bind the audited candidate inventory."}, {"path": "data/raw/vi_company/raw_data.csv", "sha256": company_hash, "rows": 10400, "note": "R1 manifest-matched hash; selected review candidates bind to this source. Source-use remains subject to R1."}],
    "records": records,
}
MASTER.write_text(json.dumps(master, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

vi = audit["sources"]["vi_company"]
selected = ["CEO", "EPS", "MOU", "NAV", "NIM", "ROA", "E&C", "N.Q"]
reason_by_tag = {"CEO": "company acronym is also a common executive-role term; article context includes both", "EPS": "financial metric acronym; potential company-tag/metric collision", "MOU": "common document acronym; potential non-issuer tag", "NAV": "financial metric acronym; potential non-issuer tag", "NIM": "banking metric acronym; potential issuer/metric collision", "ROA": "financial metric acronym; potential non-issuer tag", "E&C": "nonstandard punctuation format; alias identity unverified", "N.Q": "nonstandard punctuation format; alias identity unverified"}
queue = []
for tag in selected:
    rows = vi["raw_tag_frequencies"].get(tag, 0)
    queue.append({"candidate_id": f"VI-TAG-{tag}", "source_dataset": "VI_COMPANY", "raw_tag": tag, "normalized_candidate": tag.upper(), "alias_type": "unknown", "affected_rows": rows, "priority": "P0" if tag == "CEO" else "P1", "review_status": "needs_review", "classification": "heuristic_warning_not_confirmed_error", "reason": reason_by_tag[tag], "verification_reference": None, "mapping": None, "decision": "No correction or company mapping assigned; inspect source provenance and independently verify before Gold use."})
queue_doc = {"task": "T-012 R2", "version": "1.0.0", "created_at": "2026-10-27", "scope": "All 29 Silver codes are represented in master; selected high-risk VI tags only, not all 910 VI tags.", "source_files": [{"path": "data/silver/phobert_dataset.csv", "sha256": silver_hash, "rows": 1630}, {"path": "data/raw/vi_company/raw_data.csv", "sha256": company_hash, "rows": 10400}], "silver_ticker_candidates": [{"raw_tag": c, "normalized_candidate": c, "frequency": silver[c], "review_status": "verified_as_of_reference" if any(r["security_code"] == c for r in records) else "needs_review", "master_record_id": f"T012-R2-SILVER-{c}" if c in silver else None, "priority_rank": n + 1} for n, c in enumerate(sorted(silver, key=lambda x: (-silver[x], x)))], "vi_company_review_candidates": queue, "other_target_bearing_datasets": {"SEntFiN": "not included: entity strings are outside this bounded Vietnamese issuer scope; identity and license gates remain separate", "Thai": "not included: R6-C taxonomy/granularity is the relevant subtask; no mapping attempted"}}
QUEUE.write_text(json.dumps(queue_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"master_records": len(records), "silver_candidates": len(silver), "silver_rows": sum(silver.values()), "vi_review_candidates": len(queue), "vi_affected_rows": sum(x["affected_rows"] for x in queue)}, ensure_ascii=False))
