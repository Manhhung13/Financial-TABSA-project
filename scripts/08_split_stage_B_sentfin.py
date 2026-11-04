"""Reproducible, group-safe SEntFiN 70/15/15 split."""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/stage_B/sentfin_clean.csv"
AUDIT = ROOT / "reports/stage_B_sentfin_near_duplicates.json"
import os

SPLIT_VERSION = os.environ.get(
    "STAGE_B_SPLIT_VERSION", "split_v1"
)

if SPLIT_VERSION not in {"split_v1", "split_v2"}:
    raise ValueError("Unsupported Stage B split version")

OUT = ROOT / "data/processed/stage_B" / SPLIT_VERSION

SEED = 42
RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}
LABELS = ["negative", "neutral", "positive"]

df = pd.read_csv(SOURCE, dtype=str).fillna("")
report = json.loads(AUDIT.read_text(encoding="utf-8"))

assert df["text_hash"].nunique() == report["unique_documents"]
assert df.groupby("text_hash")["text"].nunique().max() == 1
assert set(df["sentiment"]) == set(LABELS)
assert not df.duplicated(
    ["text_hash", "target", "sentiment"]
).any()

hashes = set(df["text_hash"])
parent = {h: h for h in hashes}

def find(h):
    while parent[h] != h:
        parent[h] = parent[parent[h]]
        h = parent[h]
    return h

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[max(ra, rb)] = min(ra, rb)

pairs = report["pairs"]
assert len(pairs) == report["potential_near_duplicate_pairs"]

for pair in pairs:
    a, b = pair["left_hash"], pair["right_hash"]
    if a not in parent or b not in parent:
        raise ValueError("Near-duplicate report does not match clean data")
    union(a, b)

# Each group is indivisible across train, validation and test.
group_rows = defaultdict(list)
group_docs = defaultdict(set)

for i, h in enumerate(df["text_hash"]):
    root = find(h)
    group_rows[root].append(i)
    group_docs[root].add(h)

multi_groups = sum(len(v) > 1 for v in group_docs.values())
assert multi_groups == report["multi_document_groups"]

blocks = []
for root, indices in group_rows.items():
    counts = Counter(df.iloc[indices]["sentiment"])
    blocks.append((root, indices, counts))

rng = random.Random(SEED)
rng.shuffle(blocks)
blocks.sort(key=lambda b: len(b[1]), reverse=True)

overall = Counter(df["sentiment"])
target_rows = {
    s: len(df) * ratio for s, ratio in RATIOS.items()
}
target_labels = {
    s: {
        label: overall[label] * ratio
        for label in LABELS
    }
    for s, ratio in RATIOS.items()
}

sizes = Counter()
label_sizes = {s: Counter() for s in RATIOS}
assignments = {}

def score(split, counts, count):
    """Incremental imbalance cost for row and label quotas."""
    desired = target_rows[split]
    before = (sizes[split] - desired) ** 2 / desired
    after = (sizes[split] + count - desired) ** 2 / desired
    change = after - before

    for label in LABELS:
        desired_label = max(target_labels[split][label], 1)
        old = label_sizes[split][label]
        new = old + counts[label]
        change += 0.5 * (
            (new - desired_label) ** 2
            - (old - desired_label) ** 2
        ) / desired_label

    return change

for root, indices, counts in blocks:
    split = min(
        RATIOS,
        key=lambda s: score(s, counts, len(indices))
    )
    sizes[split] += len(indices)
    label_sizes[split].update(counts)

    for i in indices:
        assignments[i] = split

df["leakage_group"] = df["text_hash"].map(find)
df["split"] = [assignments[i] for i in range(len(df))]

# Validate document groups and every flagged near-duplicate pair.
assert df.groupby("text_hash")["split"].nunique().max() == 1
assert df.groupby("leakage_group")["split"].nunique().max() == 1

hash_split = df.groupby("text_hash")["split"].first().to_dict()
cross_pairs = sum(
    hash_split[p["left_hash"]] != hash_split[p["right_hash"]]
    for p in pairs
)
assert cross_pairs == 0

assert df.groupby("source_id")["split"].nunique().max() == 1
assert len(assignments) == len(df)

OUT.mkdir(parents=True, exist_ok=True)
summary = {}

print("=== STAGE B GROUP-SAFE SPLIT ===")
print("Total rows:", len(df))
print("Unique texts:", len(hashes))
print("Leakage groups:", len(group_rows))
print("Near-duplicate pairs:", len(pairs))
print("Cross-split candidate pairs:", cross_pairs)

for split in RATIOS:
    part = df[df["split"] == split].drop(columns=["split"])
    assert not part.empty
    path = OUT / f"sentfin_{split}.csv"
    part.to_csv(path, index=False, encoding="utf-8-sig")

    distribution = part["sentiment"].value_counts().to_dict()
    summary[split] = {
        "rows": len(part),
        "documents": part["text_hash"].nunique(),
        "groups": part["leakage_group"].nunique(),
        "labels": distribution
    }
    print(f"\n{split.upper()}:")
    print("Rows:", len(part))
    print("Documents:", summary[split]["documents"])
    print("Labels:", distribution)

manifest = {
    "seed": SEED,
    "source": str(SOURCE.relative_to(ROOT)),
    "near_duplicate_report": str(AUDIT.relative_to(ROOT)),
    "policy": "Conservative provisional near-duplicate groups",
    "target_ratios": RATIOS,
    "cross_split_candidate_pairs": cross_pairs,
    "splits": summary,
    "limitations": [
        "Near-duplicate pairs are heuristic and unreviewed.",
        "Same-event leakage not fully excluded.",
        "Test must not be used for model selection."
    ]
}

(OUT / "split_manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\nSTAGE B GROUP-SAFE SPLIT: PASS")
