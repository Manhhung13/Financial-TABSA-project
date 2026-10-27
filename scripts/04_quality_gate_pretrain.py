#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CPU-only pretraining label-quality and leakage audit for Financial TABSA.

This script NEVER trains, edits, or relabels the original datasets.
Use it to collect *candidates* for expert review, not to assert that a dataset is Gold.

Dependencies: pandas, numpy, scikit-learn.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    import numpy as np
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import cohen_kappa_score
except ImportError as exc:
    print(f"[ERROR] Missing dependency: {exc}. Install: python -m pip install pandas numpy scikit-learn")
    raise SystemExit(2)

TEXT_NAMES = [
    "text", "clean_text", "text_clean", "text_normalized", "normalized_text",
    "headline", "news_headline", "title", "news_title", "article_title",
    "sentence", "sentences", "content", "news_content", "article_content",
    "body", "article", "text_content", "review", "review_text", "raw_text",
    "text_vi", "original_text", "input_text", "document", "news_text",
    "post_text", "text_data", "company_text", "message", "paragraph",
]
TARGET_NAMES = ["target", "target_entity", "entity", "entity_name", "ticker", "symbol", "stock_code", "company", "company_name", "company_code"]
ASPECT_NAMES = ["aspect", "aspect_label", "aspect_category", "aspect_name", "category_aspect", "topic_aspect", "category"]
SENTIMENT_NAMES = [
    "sentiment", "sentiment_label", "sentiment_raw", "label_sentiment", "polarity",
    "overall_sentiment", "overall_label", "sentiment_class", "label", "class", "label_id",
]
ID_NAMES = ["article_id", "news_id", "story_id", "source_article_id", "doc_id", "document_id"]
URL_NAMES = ["url", "article_url", "source_url", "news_url", "link", "source_link"]
EVENT_NAMES = ["event_id", "event_cluster", "event_cluster_id", "cluster_id"]
THAI_ASPECTS = {
    "Profit/Loss", "Social&People", "Governance", "Product/Service", "Economics",
    "Others", "Environment", "Investment", "Financing", "Legal", "Brand",
    "Political", "Technology", "Dividend", "M&A", "Rating",
}
CANONICAL_INPUTS = [
    ("vi_company_candidates.csv", "vi", "metadata", "none"),
    ("vi_company_dapt_candidates.csv", "vi", "dapt", "none"),
    ("vi_company_suspicious_tags.csv", "vi", "review", "none"),
    ("en_sentfin_entity_sentiment.csv", "en", "supervised", "none"),
    ("th_finance_aspect_original.csv", "th", "supervised", "none"),
    ("vi_sentiment_train_unverified.csv", "vi", "supervised", "train"),
    ("vi_sentiment_val_unverified.csv", "vi", "supervised", "val"),
    ("vi_sentiment_test_unverified.csv", "vi", "supervised", "test"),
]


def norm_col(col: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(col).lower().strip()).strip("_")


def choose_column(columns, preferred) -> str | None:
    normalized = {norm_col(c): c for c in columns}
    for col in preferred:
        if col in normalized:
            return normalized[col]
    return None


def norm_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or ""))
    value = re.sub(r"[\u200b-\u200d\ufeff]", "", value)
    return " ".join(value.casefold().split())


def norm_similarity_text(value: str) -> str:
    value = norm_text(value)
    # Strip most punctuation, but keep Unicode words and spaces (including Vietnamese/Thai)
    return " ".join(re.sub(r"[^\w\s]", " ", value).split())[:1600]


def norm_url(value: str) -> str:
    value = str(value or "").strip()
    if not value or not value.startswith(("http://", "https://")):
        return ""
    try:
        u = urlsplit(value)
        query = urlencode([(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
                           if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}])
        return urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path.rstrip("/"), query, ""))
    except ValueError:
        return ""


def clip(value, n=240):
    value = str(value)
    return value if len(value) <= n else value[:n] + " ..."


def read_frame(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path, dtype=str, keep_default_na=False, encoding="utf-8-sig", low_memory=False)
    if suffix == ".jsonl":
        return pd.read_json(file_path, lines=True, dtype=False).fillna("").astype(str)
    if suffix == ".parquet":
        return pd.read_parquet(file_path).fillna("").astype(str)
    raise ValueError(f"Unsupported extension: {suffix}")


def discover_sources(project: Path, silver_path: str | None) -> list[dict]:
    sources = []
    seen = set()
    for name, language, role, split in CANONICAL_INPUTS:
        f = project / "data" / "processed" / name
        if f.exists():
            sources.append(dict(path=f, name=name, lang=language, role=role, split=split))
            seen.add(f.resolve())
    extras = []
    data_dir = project / "data"
    if data_dir.exists():
        extras += [f for f in data_dir.rglob("*") if f.is_file() and f.suffix.lower() in {".csv", ".jsonl", ".parquet"}
                   and ("silver" in f.name.lower() or "gold" in f.parts)]
    if silver_path:
        f = Path(silver_path)
        if not f.is_absolute():
            f = project / f
        if f.is_dir():
            extras.extend(f.rglob("*.csv"))
            extras.extend(f.rglob("*.jsonl"))
            extras.extend(f.rglob("*.parquet"))
        else:
            extras.append(f)
    for f in sorted(set(extras)):
        if not f.exists() or f.resolve() in seen:
            continue
        parts = [p.lower() for p in f.parts]
        role = "gold" if "gold" in parts else "silver" if "silver" in f.name.lower() or "silver" in parts else "extra"
        split = "test" if re.search(r"(^|[_\-.])test([_\-.]|$)", f.name.lower()) else "val" if re.search(r"(^|[_\-.])(val|valid|validation)([_\-.]|$)", f.name.lower()) else "train" if re.search(r"(^|[_\-.])train([_\-.]|$)", f.name.lower()) else "none"
        sources.append(dict(path=f, name=str(f.relative_to(project)) if f.is_relative_to(project) else str(f),
                            lang="vi", role=role, split=split))
        seen.add(f.resolve())
    return sources


def detect_text_col(df: pd.DataFrame) -> tuple[str | None, str]:
    c = choose_column(df.columns, TEXT_NAMES)
    if c:
        return c, "alias"
    # Heuristic is intentionally conservative. Never silently guess for tiny columns.
    excluded = set(TARGET_NAMES + ASPECT_NAMES + SENTIMENT_NAMES + ID_NAMES + URL_NAMES + EVENT_NAMES)
    ranked = []
    for col in df.columns:
        if norm_col(col) in excluded or len(df) == 0:
            continue
        values = df[col].astype(str).head(300)
        lengths = values.map(lambda s: len(s.strip()))
        nonempty = lengths[lengths > 0]
        if len(nonempty) < max(2, len(values) // 3):
            continue
        median = float(nonempty.median())
        if median >= 30:
            ranked.append((median, col))
    if len(ranked) == 1:
        return ranked[0][1], "heuristic_single_candidate"
    return None, "ambiguous_or_missing"


def create_canonical(df: pd.DataFrame, source: dict, text_col: str) -> pd.DataFrame:
    cols = df.columns
    field_cols = {
        "target": choose_column(cols, TARGET_NAMES),
        "aspect": choose_column(cols, ASPECT_NAMES),
        "sentiment": choose_column(cols, SENTIMENT_NAMES),
        "article_id": choose_column(cols, ID_NAMES),
        "url": choose_column(cols, URL_NAMES),
        "event_id": choose_column(cols, EVENT_NAMES),
    }
    result = pd.DataFrame(index=df.index)
    result["source"] = source["name"]
    result["role"] = source["role"]
    result["split"] = source["split"]
    result["lang"] = source["lang"]
    result["source_row"] = df.index + 2
    result["text"] = df[text_col].astype(str)
    for field, col in field_cols.items():
        result[field] = df[col].astype(str) if col else ""
    result["norm"] = result["text"].map(norm_text)
    result["simtext"] = result["text"].map(norm_similarity_text)
    result["target_norm"] = result["target"].map(norm_text)
    result["aspect_norm"] = result["aspect"].map(norm_text)
    result["url_norm"] = result["url"].map(norm_url)
    result["article_id_norm"] = result["article_id"].map(norm_text)
    result["event_id_norm"] = result["event_id"].map(norm_text)
    return result.reset_index(drop=True)


def add_label_diagnostics(can: pd.DataFrame, source: dict, stats_rows: list, conflicts: list):
    if source["role"] not in {"supervised", "silver", "gold"}:
        return
    for field in ("sentiment", "aspect"):
        counts = can[field].value_counts(dropna=False)
        for val, count in counts.items():
            stats_rows.append({"source": source["name"], "field": field,
                               "raw_value": val if val else "[MISSING]", "count": int(count)})
    # One text may legitimately have multiple entity/aspect targets. Compare within same target+aspect only.
    labeled = can.loc[(can["norm"] != "") & (can["sentiment"] != "")].copy()
    if labeled.empty:
        return
    for (txt, tgt, asp), group in labeled.groupby(["norm", "target_norm", "aspect_norm"], sort=False):
        labels = sorted(set(group["sentiment"].astype(str).str.strip().str.casefold()))
        if len(labels) > 1:
            conflicts.append({
                "source": source["name"], "target": clip(group["target"].iloc[0], 80),
                "aspect": clip(group["aspect"].iloc[0], 80),
                "sentiments": " | ".join(labels), "rows": len(group),
                "row_numbers": ",".join(map(str, group["source_row"].head(12).tolist())),
                "text_excerpt": clip(group["text"].iloc[0]),
                "confidence": "candidate_only" if not tgt else "same_target_and_aspect",
            })


def select_review_sample(can: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    eligible = can.loc[can["text"].astype(str).str.strip().ne("")].copy()
    if eligible.empty or n <= 0:
        return eligible.iloc[0:0]
    eligible = eligible.drop_duplicates(["norm", "target_norm", "aspect_norm"], keep="first")
    # Give rare classes a chance; this is a PILOT review, not a statistical certification.
    key = "aspect" if (eligible["aspect"].ne("").sum() > 0 and eligible["aspect"].nunique() > 1) else "sentiment"
    rng = np.random.default_rng(seed)
    groups = {}
    for label, g in eligible.groupby(key, dropna=False):
        indices = g.index.to_numpy().copy()
        rng.shuffle(indices)
        groups[str(label)] = list(indices)
    selected = []
    # Alternating classes instead of proportional-only sampling.
    while len(selected) < min(n, len(eligible)) and any(groups.values()):
        for label in sorted(groups, key=lambda k: (len(groups[k]), k)):
            if groups[label] and len(selected) < min(n, len(eligible)):
                selected.append(groups[label].pop())
    return eligible.loc[selected].copy()


def record_of(row) -> dict:
    return {"source": row.source, "source_row": int(row.source_row),
            "text": clip(row.text, 330), "target": clip(row.target, 70),
            "aspect": clip(row.aspect, 60), "sentiment": clip(row.sentiment, 60)}


def make_pair_specs(frames: dict[str, pd.DataFrame]) -> list[tuple[str, str, str]]:
    def filter_keys(role=None, split=None):
        out = []
        for k, df in frames.items():
            row = df.iloc[0] if len(df) else None
            if row is None or row.lang != "vi":
                continue
            if role and row.role != role:
                continue
            if split and row.split != split:
                continue
            out.append(k)
        return out
    training = filter_keys(role="supervised", split="train") + filter_keys(role="gold", split="train")
    validations = filter_keys(role="supervised", split="val") + filter_keys(role="gold", split="val")
    testing = filter_keys(role="supervised", split="test") + filter_keys(role="gold", split="test")
    dapt = filter_keys(role="dapt")
    silver = filter_keys(role="silver")
    pairs = []
    def add(lhs, rhs, purpose):
        for a in lhs:
            for b in rhs:
                if a != b:
                    pairs.append((a, b, purpose))
    add(validations, training, "val_vs_train")
    add(testing, training, "test_vs_train")
    add(testing, validations, "test_vs_val")
    add(validations + testing, dapt, "heldout_vs_dapt")
    add(validations + testing, silver, "heldout_vs_silver")
    add(testing, filter_keys(role="gold", split="none"), "test_vs_unsplit_gold")
    # De-duplicate reverse pair comparisons.
    unique, seen = [], set()
    for left, right, purpose in pairs:
        key = (left, right, purpose)
        if key not in seen:
            seen.add(key)
            unique.append((left, right, purpose))
    return unique


def exact_overlap(left: pd.DataFrame, right: pd.DataFrame, purpose: str,
                  max_per_key=3, max_total=1500) -> list[dict]:
    results = []
    for field, typ in [("norm", "exact_text"), ("url_norm", "same_url"),
                       ("event_id_norm", "same_event_id"),
                       ("article_id_norm", "same_article_id_check_source_namespace")]:
        a = left.loc[left[field].ne("")].drop_duplicates(field).set_index(field, drop=False)
        b = right.loc[right[field].ne("")].drop_duplicates(field).set_index(field, drop=False)
        common = a.index.intersection(b.index)
        for key in common[:max_total]:
            ra, rb = a.loc[key], b.loc[key]
            results.append({"check": purpose, "kind": typ, "similarity": 1.0,
                            "left_source": ra["source"], "left_row": int(ra["source_row"]),
                            "right_source": rb["source"], "right_row": int(rb["source_row"]),
                            "left_target": clip(ra["target"], 80), "right_target": clip(rb["target"], 80),
                            "left_text": clip(ra["text"], 300), "right_text": clip(rb["text"], 300),
                            "shared_key": clip(key, 160)})
            if len(results) >= max_total:
                return results
    return results


def near_overlaps(frames: dict[str, pd.DataFrame], pairs: list, threshold: float,
                  per_pair_limit=400) -> tuple[list[dict], str]:
    wanted = {p for a, b, _ in pairs for p in (a, b)}
    pool = {}
    for source in sorted(wanted):
        df = frames[source]
        val = df.loc[df["simtext"].str.len().ge(35)].drop_duplicates("simtext", keep="first").copy()
        if not val.empty:
            pool[source] = val.reset_index(drop=True)
    if not pool:
        return [], "No VI text >=35 characters eligible for near-duplicate check"
    # One global vectorizer saves repeatedly fitting for each pair. This ONLY finds
    # lexical near-duplicates within the same language (not semantic paraphrases).
    corpus = pd.concat([d["simtext"] for d in pool.values()], ignore_index=True)
    vec = TfidfVectorizer(analyzer="char", ngram_range=(3, 5),
                          min_df=1, max_features=100000, dtype=np.float32, sublinear_tf=True)
    try:
        matrix = vec.fit_transform(corpus.tolist())
    except ValueError as e:
        return [], f"Near-duplicate vectorizer failed: {e}"
    matrices = {}
    start = 0
    for source, df in pool.items():
        matrices[source] = matrix[start:start + len(df)]
        start += len(df)
    found = []
    for left_key, right_key, purpose in pairs:
        if left_key not in pool or right_key not in pool:
            continue
        left, right = pool[left_key], pool[right_key]
        lm, rm = matrices[left_key], matrices[right_key]
        n_out = 0
        for start in range(0, len(left), 24):
            q = lm[start:start + 24]
            scores = (q @ rm.T).tocsr()
            for i in range(scores.shape[0]):
                r0, r1 = scores.indptr[i], scores.indptr[i+1]
                if r1 == r0:
                    continue
                columns = scores.indices[r0:r1]
                similarities = scores.data[r0:r1]
                above = np.flatnonzero(similarities >= threshold)
                if len(above) == 0:
                    continue
                top = above[np.argsort(similarities[above])[-4:][::-1]]
                for z in top:
                    j = int(columns[z])
                    a = left.iloc[start+i]
                    b = right.iloc[j]
                    if a["norm"] == b["norm"]:
                        continue  # covered by exact overlap
                    found.append({
                        "check": purpose, "kind": "similar_text_needs_manual_review",
                        "similarity": round(float(similarities[z]), 4),
                        "left_source": a["source"], "left_row": int(a["source_row"]),
                        "right_source": b["source"], "right_row": int(b["source_row"]),
                        "left_target": clip(a["target"], 80), "right_target": clip(b["target"], 80),
                        "left_text": clip(a["text"], 330), "right_text": clip(b["text"], 330),
                        "shared_key": "",
                    })
                    n_out += 1
                    if n_out >= per_pair_limit:
                        break
                if n_out >= per_pair_limit:
                    break
            if n_out >= per_pair_limit:
                break
        print(f"[NEAR] {purpose}: {left_key} vs {right_key} -> {n_out} candidate pair(s)")
    found.sort(key=lambda x: x["similarity"], reverse=True)
    return found, "Lexical similarity using Vietnamese character 3-5-gram TF-IDF; semantic/event-level matching is NOT guaranteed"


def save_csv(rows, dest: Path, columns: list[str]):
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=columns)
    else:
        df = df.reindex(columns=columns)
    df.to_csv(dest, index=False, encoding="utf-8-sig")


def mode_score_reviews(out: Path) -> int:
    a = out / "blind_review_annotator_1.csv"
    b = out / "blind_review_annotator_2.csv"
    if not a.exists() or not b.exists():
        print("[ERROR] Run initial audit first. Both annotator CSV files must exist.")
        return 2
    d1 = pd.read_csv(a, keep_default_na=False, dtype=str)
    d2 = pd.read_csv(b, keep_default_na=False, dtype=str)
    merged = d1.merge(d2, on="review_id", suffixes=("_1", "_2"), how="inner")
    disagreements = []
    metrics = []
    for field in ["aspect_annotation", "sentiment_annotation", "target_annotation"]:
        left = f"{field}_1"
        right = f"{field}_2"
        if left not in merged or right not in merged:
            continue
        a_labels = merged[left].map(norm_text)
        b_labels = merged[right].map(norm_text)
        mask = a_labels.ne("") & b_labels.ne("")
        if not mask.any():
            continue
        aa, bb = a_labels[mask], b_labels[mask]
        # Kappa is undefined if both reviewers assign the same single class to all items.
        distinct = set(aa.tolist()) | set(bb.tolist())
        kappa = round(float(cohen_kappa_score(aa.tolist(), bb.tolist())), 4) if len(distinct) > 1 else "N/A (single class)"
        metric = {"task": field, "reviewed_pairs": int(mask.sum()),
                  "observed_agreement": round(float(aa.eq(bb).mean()), 4),
                  "cohen_kappa": kappa}
        metrics.append(metric)
        mismatch = merged.loc[mask & a_labels.ne(b_labels), ["review_id", left, right]].copy()
        mismatch["field"] = field
        disagreements.extend(mismatch.to_dict("records"))
    save_csv(metrics, out / "annotation_agreement.csv", ["task", "reviewed_pairs", "observed_agreement", "cohen_kappa"])
    save_csv(disagreements, out / "reviewer_disagreements.csv", ["review_id", "field", "aspect_annotation_1", "aspect_annotation_2", "sentiment_annotation_1", "sentiment_annotation_2", "target_annotation_1", "target_annotation_2"])
    # Compare consensus against original labels ONLY when the original label is
    # explicitly comparable. VI codes 0/1/2 are NOT semantically defined here.
    key_file = out / "review_lookup_original_labels_PRIVATE.csv"
    original_disagreements = []
    comparable = Counter()
    matching = Counter()
    if key_file.exists():
        lookup = pd.read_csv(key_file, dtype=str, keep_default_na=False)
        merged_key = merged.merge(lookup, on="review_id", how="left")
        for r in merged_key.to_dict("records"):
            for task in ("aspect", "sentiment"):
                x = norm_text(r.get(f"{task}_annotation_1", ""))
                y = norm_text(r.get(f"{task}_annotation_2", ""))
                if not x or not y or x != y:
                    continue
                raw = norm_text(r.get(f"{task}_original", ""))
                if not raw:
                    continue
                if task == "sentiment" and raw in {"0", "1", "2", "0.0", "1.0", "2.0"}:
                    continue  # Require independent verification of the source codebook.
                comparable[task] += 1
                if x == raw:
                    matching[task] += 1
                else:
                    original_disagreements.append({"review_id": r["review_id"],
                                                   "source": r.get("source", ""),
                                                   "task": task, "original": raw,
                                                   "both_annotators_agree_on": x,
                                                   "action": "Adjudicate; verify definitions and target"})
    save_csv(original_disagreements, out / "original_label_disagreements.csv",
             ["review_id", "source", "task", "original", "both_annotators_agree_on", "action"])
    for task in comparable:
        print(f"[LABEL] {task}: agreement with original labels among comparable reviewer-consensus rows = {matching[task]}/{comparable[task]}")
    print("[WARN] Original label agreement EXCLUDES unmapped 0/1/2 VI sentiment codes")
    if metrics:
        print(pd.DataFrame(metrics).to_string(index=False))
    else:
        print("[WARN] Both reviewers must independently fill *_annotation columns first")
    print(f"[OUT] {out / 'reviewer_disagreements.csv'}")
    print("[WARN] Kappa/agreements are diagnostics, NOT automatic Gold certification; adjudicate disputes.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="CPU-only pretraining audit: label quality + data leakage")
    ap.add_argument("--project", type=Path, default=Path.cwd(), help="Your Financial TABSA project root")
    ap.add_argument("--out", type=Path, default=None, help="Audit output folder")
    ap.add_argument("--silver", type=str, default=None, help="Optional Silver CSV/JSONL/parquet path or folder")
    ap.add_argument("--sample-size", type=int, default=60, help="Blinded review samples per labeled source")
    ap.add_argument("--near-threshold", type=float, default=0.85, help="Near-duplicate lexical similarity threshold")
    ap.add_argument("--score-review", action="store_true", help="Score the two completed blind annotation files")
    args = ap.parse_args()
    project = args.project.resolve()
    out = (args.out or (project / "reports" / "pretrain_quality")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.score_review:
        return mode_score_reviews(out)
    if not (0.65 <= args.near_threshold <= 0.99):
        ap.error("--near-threshold must be between 0.65 and 0.99")
    sources = discover_sources(project, args.silver)
    if not sources:
        print(f"[ERROR] No datasets found under {project / 'data'}. Run 03_audit_prepare.py first.")
        return 2
    print(f"[INFO] Project: {project}")
    print(f"[INFO] Found {len(sources)} candidate source files")
    schemas, label_stats, conflicts, frames, audit_samples = [], [], [], {}, []
    warnings = [
        "VI sentiment code mapping 0/1/2 is UNVERIFIED: inspect dataset documentation; never auto-map.",
        "SEntFiN is ENTITY sentiment; Thai is ASPECT+sentiment. Task/head mismatch requires explicit modeling.",
        "40 suspect VI company tags and 13 SEntFiN parse warnings were present in prior step; review upstream records.",
        "Silver pseudo-labels never automatically become Gold; LLM score=0 is not proof of neutrality/absence.",
        "Exact/lexical similarity cannot detect translated/semantically paraphrased duplicates or same-event articles.",
        "Grouping by article/event should occur BEFORE train/validation/test splitting and augmentation.",
    ]
    for source in sources:
        try:
            raw = read_frame(source["path"])
        except Exception as exc:
            msg = f"Could not read {source['name']}: {type(exc).__name__}: {exc}"
            warnings.append(msg)
            print(f"[WARN] {msg}")
            continue
        txt_col, reason = detect_text_col(raw)
        s_col = choose_column(raw.columns, SENTIMENT_NAMES)
        a_col = choose_column(raw.columns, ASPECT_NAMES)
        t_col = choose_column(raw.columns, TARGET_NAMES)
        schemas.append({
            "source": source["name"], "language": source["lang"], "role": source["role"],
            "split": source["split"], "rows": len(raw), "column_names": " | ".join(raw.columns),
            "text_col": txt_col or "[UNRESOLVED]", "text_detection": reason,
            "target_col": t_col or "", "aspect_col": a_col or "", "sentiment_col": s_col or "",
            "missing_text": int(raw[txt_col].astype(str).str.strip().eq("").sum()) if txt_col else len(raw),
            "missing_sentiment": int(raw[s_col].astype(str).str.strip().eq("").sum()) if s_col else "[NO COLUMN]",
            "distinct_sentiments": " | ".join(sorted(raw[s_col].astype(str).unique())[:30]) if s_col else "",
        })
        if not txt_col:
            warnings.append(f"Cannot safely infer text field for {source['name']}; inspect schema.csv and rename/configure columns")
            print(f"[WARN] {source['name']} missing identifiable text column; skipped leakage checks")
            continue
        can = create_canonical(raw, source, txt_col)
        frames[source["name"]] = can
        add_label_diagnostics(can, source, label_stats, conflicts)
        if source["role"] in {"supervised", "silver", "gold"}:
            audit_samples.append(select_review_sample(can, args.sample_size, seed=42 + len(audit_samples)))
        if source["lang"] == "th" and source["role"] == "supervised":
            if a_col:
                bad = {x for x in can["aspect"].unique() if x and x not in THAI_ASPECTS}
                if bad:
                    warnings.append(f"Thai aspect values outside 16-category list for {source['name']}: {sorted(bad)[:20]}")
            if s_col:
                bad = {x for x in can["sentiment"].unique() if x and x.casefold() not in {"neutral", "positive", "negative"}}
                if bad:
                    warnings.append(f"Thai sentiment values outside Positive/Neutral/Negative for {source['name']}: {sorted(bad)[:20]}")
        if source["role"] in {"supervised", "gold"} and not s_col:
            warnings.append(f"No sentiment column found in {source['name']}; please inspect before training")
        print(f"[DATA] {source['name']}: {len(can)} rows; text={txt_col}; sentiment={s_col}; aspect={a_col}; target={t_col}")
    if not frames:
        print("[ERROR] None of the input files had a reliably detected text column. See schema.csv")
    save_csv(schemas, out / "schema.csv", ["source", "language", "role", "split", "rows", "column_names", "text_col", "text_detection", "target_col", "aspect_col", "sentiment_col", "missing_text", "missing_sentiment", "distinct_sentiments"])
    save_csv(label_stats, out / "label_distribution.csv", ["source", "field", "raw_value", "count"])
    save_csv(conflicts, out / "label_conflicts.csv", ["source", "target", "aspect", "sentiments", "rows", "row_numbers", "text_excerpt", "confidence"])
    pairs = make_pair_specs(frames)
    exact_records = []
    for lk, rk, why in pairs:
        found = exact_overlap(frames[lk], frames[rk], why)
        exact_records.extend(found)
        print(f"[EXACT] {why}: {lk} vs {rk} -> {len(found)} match(es)")
    overlap_fields = ["check", "kind", "similarity", "left_source", "left_row", "right_source", "right_row", "left_target", "right_target", "left_text", "right_text", "shared_key"]
    save_csv(exact_records, out / "cross_split_exact.csv", overlap_fields)
    near_records, near_method = near_overlaps(frames, pairs, args.near_threshold)
    save_csv(near_records, out / "cross_split_near.csv", overlap_fields)
    review_key, blind = [], []
    if audit_samples:
        combined = pd.concat(audit_samples, ignore_index=True)
        for r in combined.itertuples():
            token = hashlib.sha1(f"{r.source}:{r.source_row}:{r.norm}".encode("utf-8")).hexdigest()[:15]
            review_id = "REV-" + token.upper()
            blind.append({"review_id": review_id, "language": r.lang, "text": r.text,
                          "target": r.target, "aspect_annotation": "", "sentiment_annotation": "",
                          "target_annotation": "", "uncertain": "", "comment": ""})
            review_key.append({"review_id": review_id, "source": r.source, "source_row": r.source_row,
                               "aspect_original": r.aspect, "sentiment_original": r.sentiment,
                               "target_original": r.target})
    review_cols = ["review_id", "language", "text", "target", "aspect_annotation", "sentiment_annotation", "target_annotation", "uncertain", "comment"]
    save_csv(blind, out / "blind_review_annotator_1.csv", review_cols)
    save_csv(blind, out / "blind_review_annotator_2.csv", review_cols)
    save_csv(review_key, out / "review_lookup_original_labels_PRIVATE.csv", ["review_id", "source", "source_row", "aspect_original", "sentiment_original", "target_original"])
    has_silver = any(df.iloc[0]["role"] == "silver" for df in frames.values() if len(df))
    has_gold = any(df.iloc[0]["role"] == "gold" for df in frames.values() if len(df))
    if not has_silver:
        warnings.append("Silver dataset was not discovered: pass --silver path_to_file_or_folder; Silver leakage NOT checked")
    if not has_gold:
        warnings.append("No manually verified Gold dataset found/attested; an automated audit cannot create one")
    summary = {
        "status": "MANUAL_REVIEW_REQUIRED",
        "safe_to_start_final_supervised_training": False,
        "reason": "Original label definitions, double-blind annotations, and event-level leakage review require human validation.",
        "sources_read": len(frames),
        "cross_split_pair_checks": len(pairs),
        "exact_matches_to_investigate": len(exact_records),
        "near_duplicate_candidates_to_investigate": len(near_records),
        "label_conflict_groups_to_investigate": len(conflicts),
        "blinded_examples_per_annotator": len(blind),
        "gold_files_found_not_necessarily_verified": has_gold,
        "silver_files_checked": has_silver,
        "near_threshold": args.near_threshold,
        "near_method_and_limitations": near_method,
        "warnings": warnings,
        "quality_gates": [
            "Verify raw source and exact meaning of ALL sentiment/aspect labels (esp. Vietnamese codes 0/1/2)",
            "Review parse warnings, suspected tags, and conflicting label rows",
            "Two independent blinded annotators + adjudication; preserve a versioned Gold test set",
            "Resolve each exact/near match crossing train/validation/test, Silver, and DAPT",
            "Group by article_id/source URL/event cluster BEFORE splitting; no translation/augmentation across splits",
            "Check entity/aspect targets (same text may legitimately have different target labels)",
            "Keep held-out Gold Test untouched during model selection and continued pretraining",
        ],
    }
    with (out / "audit_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\n== QUALITY GATE SUMMARY ==")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"warnings", "quality_gates", "near_method_and_limitations", "reason"}}, ensure_ascii=False, indent=2))
    print(f"[OUT] {out}")
    print("[NEXT] Examine schema.csv, label_conflicts.csv, cross_split_exact.csv, cross_split_near.csv")
    print("[NEXT] Distribute TWO blind reviewer CSV files separately; keep PRIVATE label lookup confidential")
    print("[WARN] Not a green-light for GPU training. All alerts need review, plus provenance and event checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
