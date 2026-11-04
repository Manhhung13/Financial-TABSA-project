"""Prepare SEntFiN entity-sentiment data without modifying the source."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/en_sentfin_entity_sentiment.csv"
OUT = ROOT / "data/processed/stage_B"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SOURCE, dtype=str).fillna("")

for col in ["text_hash", "text", "target", "sentiment"]:
    df[col] = df[col].str.strip()


# Recompute canonical text hashes before conflict and duplicate checks.
import hashlib
import re
import unicodedata

original_hash = df["text_hash"].copy()

df["text"] = df["text"].map(
    lambda t: " ".join(
        unicodedata.normalize("NFC", t).split()
    )
)

computed_hash = df["text"].map(
    lambda t: hashlib.sha256(
        t.casefold().encode("utf-8")
    ).hexdigest()
)

hash_mismatch = original_hash.ne(computed_hash)

hash_audit = df.loc[
    hash_mismatch,
    ["source_id", "text", "target", "sentiment", "text_hash"]
].copy()

hash_audit["corrected_hash"] = computed_hash[hash_mismatch]

hash_audit.to_csv(
    OUT / "sentfin_hash_repair_audit.csv",
    index=False, encoding="utf-8-sig"
)

print("[HASH] Mismatches corrected:", int(hash_mismatch.sum()))

df["text_hash"] = computed_hash


# SENTFIN_TARGET_REPAIR_V1
# Repair only source records confirmed in the target quality audit.
# Original SEntFiN and sentiment labels remain unchanged.

repair_ids = {
    "sentfin_304", "sentfin_1086", "sentfin_1384",
    "sentfin_2098", "sentfin_2507", "sentfin_3651",
    "sentfin_4178", "sentfin_4179", "sentfin_4549",
    "sentfin_5952", "sentfin_6787", "sentfin_8250",
    "sentfin_2008", "sentfin_4388", "sentfin_6655",
    "sentfin_8396", "sentfin_9276", "sentfin_7562",
    "sentfin_8168"
}

repairs = []

for i, row in df[
    df["source_id"].isin(repair_ids)
].iterrows():

    original = row["target"]
    text = row["text"]

    if original.casefold() in text.casefold():
        continue

    corrected = (
        original
        .replace("neutral", "hold")
        .replace("negative", "sell")
    )

    if corrected == original:
        raise ValueError(
            f"Cannot reconstruct target: {row['source_id']}"
        )

    if corrected.casefold() not in text.casefold():
        raise ValueError(
            f"Corrected target not found in headline: "
            f"{row['source_id']}"
        )

    repairs.append({
        "source_id": row["source_id"],
        "text": text,
        "original_target": original,
        "corrected_target": corrected,
        "sentiment": row["sentiment"],
        "verification": "exact_match_in_headline"
    })

    df.at[i, "target"] = corrected

repaired_ids = {r["source_id"] for r in repairs}

if repaired_ids != repair_ids or len(repairs) != 19:
    raise RuntimeError(
        f"Unexpected repair coverage: "
        f"{len(repairs)} rows / {len(repaired_ids)} IDs"
    )

pd.DataFrame(repairs).to_csv(
    OUT / "sentfin_source_target_repairs.csv",
    index=False,
    encoding="utf-8-sig"
)

print("[TARGET] Corrected source records:", len(repairs))

keys = ["text_hash", "target"]
dedup_keys = ["text_hash", "target", "sentiment"]

# Find contradictory sentiment labels for the same text-target pair.
label_counts = df.groupby(keys)["sentiment"].nunique()
conflict_keys = label_counts[label_counts > 1].index

row_keys = pd.MultiIndex.from_frame(df[keys])
conflict_mask = row_keys.isin(conflict_keys)

conflicts = df.loc[conflict_mask].copy()
eligible = df.loc[~conflict_mask].copy()

# Remove repeated identical text-target-sentiment labels.
duplicate_mask = eligible.duplicated(
    subset=dedup_keys, keep="first"
)

duplicates = eligible.loc[duplicate_mask].copy()
clean = eligible.loc[~duplicate_mask].copy()

# Validate output before writing.
assert not clean.duplicated(dedup_keys).any()
assert clean.groupby(keys)["sentiment"].nunique().max() <= 1
assert len(clean) + len(conflicts) + len(duplicates) == len(df)

clean.to_csv(
    OUT / "sentfin_clean.csv",
    index=False, encoding="utf-8-sig"
)
conflicts.to_csv(
    OUT / "sentfin_conflicts_quarantine.csv",
    index=False, encoding="utf-8-sig"
)
duplicates.to_csv(
    OUT / "sentfin_duplicates_removed.csv",
    index=False, encoding="utf-8-sig"
)

report = {
    "source": str(SOURCE.relative_to(ROOT)),
    "input_rows": len(df),
    "conflicting_text_target_groups": len(conflict_keys),
    "conflict_rows_quarantined": len(conflicts),
    "duplicate_rows_removed": len(duplicates),
    "clean_rows": len(clean),
    "clean_unique_texts": clean["text_hash"].nunique(),
    "label_distribution": clean["sentiment"].value_counts().to_dict(),
    "split_policy": "group by text_hash; not yet split",
    "conflict_policy": "quarantine all conflicting rows"
}

(OUT / "cleaning_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("=== STAGE B CLEANING REPORT ===")
for k, v in report.items():
    print(f"{k}: {v}")

print("STAGE B DATA CLEANING: PASS")
