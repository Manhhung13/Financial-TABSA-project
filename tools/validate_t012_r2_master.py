"""Read-only structural/evidence-completeness check for the T-012 R2 master."""
from __future__ import annotations

import json
from pathlib import Path


MASTER = Path(__file__).resolve().parents[1] / "reports" / "T-012_R2_issuer_alias_master.json"
REQUIRED = {
    "record_id", "alias_raw", "alias_normalized", "alias_type", "entity_type",
    "legal_name_as_evidenced", "security_code", "exchange", "reference_title",
    "reference_url", "reference_date", "evidence", "verification_method",
    "review_status", "reviewer", "reviewed_at", "rationale", "source_dataset",
    "source_row_frequency", "source_file", "source_sha256",
}


def validate(master: dict) -> list[str]:
    errors: list[str] = []
    if master.get("version") != "1.0.0":
        errors.append("version must be 1.0.0")
    seen: set[str] = set()
    for i, row in enumerate(master.get("records", [])):
        missing = sorted(k for k in REQUIRED if row.get(k) in (None, "", []))
        if missing:
            errors.append(f"records[{i}] missing required evidence fields: {', '.join(missing)}")
        code = row.get("security_code")
        if code in seen:
            errors.append(f"duplicate verified security_code: {code}")
        if code:
            seen.add(code)
        if row.get("review_status") != "verified_as_of_reference":
            errors.append(f"records[{i}] is not explicitly verified_as_of_reference")
        if row.get("alias_normalized") != code:
            errors.append(f"records[{i}] ticker alias and security code differ")
        if not isinstance(row.get("source_row_frequency"), int) or row.get("source_row_frequency", 0) < 1:
            errors.append(f"records[{i}] source_row_frequency must be positive")
        if row.get("source_sha256") and len(row["source_sha256"]) != 64:
            errors.append(f"records[{i}] source_sha256 must be a SHA-256 hex digest")
        if row.get("valid_from") is None and "valid dates beyond cited reference date are not asserted" not in row.get("rationale", "") and row.get("reference_date"):
            # Reference date is temporal evidence; unknown legal validity is acceptable only when stated.
            if "validity" not in row.get("rationale", "").lower() and "valid date" not in row.get("rationale", "").lower():
                errors.append(f"records[{i}] must state the temporal limit of the reference")
    if not master.get("records"):
        errors.append("no verified records")
    return errors


if __name__ == "__main__":
    data = json.loads(MASTER.read_text(encoding="utf-8"))
    problems = validate(data)
    print(json.dumps({"status": "PASS" if not problems else "BLOCKED", "verified_records": len(data.get("records", [])), "errors": problems}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(problems))
