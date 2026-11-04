"""Audit potential near-duplicate SEntFiN titles before splitting."""
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/stage_B/sentfin_clean.csv"
OUT = ROOT / "reports/stage_B_sentfin_near_duplicates.json"

df = pd.read_csv(SOURCE, dtype=str).fillna("")
docs = df[["text_hash", "text"]].drop_duplicates(
    "text_hash"
).reset_index(drop=True)

assert len(docs) == 10666, "Unexpected document count"
assert docs["text_hash"].nunique() == len(docs)

texts = docs["text"].tolist()
hashes = docs["text_hash"].tolist()

tokens = [
    re.findall(r"[a-z0-9]+", t.casefold())
    for t in texts
]

postings = defaultdict(list)

for i, words in enumerate(tokens):
    shingles = set(zip(words, words[1:], words[2:]))
    for shingle in shingles:
        postings[shingle].append(i)

candidates = set()

for indices in postings.values():
    if 2 <= len(indices) <= 30:
        candidates.update(combinations(indices, 2))

pairs = []
parent = list(range(len(docs)))

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(a, b):
    a, b = find(a), find(b)
    if a != b:
        parent[max(a, b)] = min(a, b)

for a, b in sorted(candidates):
    wa, wb = set(tokens[a]), set(tokens[b])
    union_tokens = wa | wb

    jac = (
        len(wa & wb) / len(union_tokens)
        if union_tokens else 0
    )

    ratio = SequenceMatcher(
        None, texts[a].casefold(), texts[b].casefold()
    ).ratio()

    if jac >= 0.82 or ratio >= 0.88:
        pairs.append({
            "left_hash": hashes[a],
            "right_hash": hashes[b],
            "left_text": texts[a],
            "right_text": texts[b],
            "token_jaccard": round(jac, 6),
            "sequence_similarity": round(ratio, 6),
            "review_status": "unreviewed"
        })
        union(a, b)

sizes = defaultdict(int)
for i in range(len(docs)):
    sizes[find(i)] += 1

multi_groups = [v for v in sizes.values() if v > 1]

report = {
    "source": str(SOURCE.relative_to(ROOT)),
    "unique_documents": len(docs),
    "candidate_pairs_compared": len(candidates),
    "potential_near_duplicate_pairs": len(pairs),
    "multi_document_groups": len(multi_groups),
    "largest_group_size": max(sizes.values()),
    "method": "rare word trigrams + token Jaccard / SequenceMatcher",
    "thresholds": {
        "token_jaccard": 0.82,
        "sequence_similarity": 0.88
    },
    "limitations": [
        "Candidate scan is heuristic and not exhaustive.",
        "Pairs have not been manually confirmed as same event."
    ],
    "pairs": pairs
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("=== STAGE B NEAR-DUPLICATE REPORT ===")
for key in [
    "unique_documents",
    "candidate_pairs_compared",
    "potential_near_duplicate_pairs",
    "multi_document_groups",
    "largest_group_size"
]:
    print(f"{key}: {report[key]}")

print("Report:", OUT)
print("STAGE B NEAR-DUPLICATE AUDIT: PASS")
