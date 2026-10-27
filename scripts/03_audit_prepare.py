"""Step 3: Parse and audit each corpus without inventing labels.

Datasets retain separate tasks; none of the outputs is a Vietnamese Gold test.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
PROC = ROOT / 'data' / 'processed'
PROC.mkdir(parents=True, exist_ok=True)
SUMMARY: dict[str, object] = {}


def clean_text(value) -> str:
    if pd.isna(value):
        return ''
    value = unicodedata.normalize('NFC', str(value))
    value = value.replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', value).strip()


def sha(value: str) -> str:
    return hashlib.sha256(clean_text(value).casefold().encode('utf-8')).hexdigest()


def save(df: pd.DataFrame, name: str) -> None:
    dst = PROC / name
    df.to_csv(dst, index=False, encoding='utf-8-sig')
    print('[OUT]', dst, 'rows=', len(df))


def read_file(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, encoding='utf-8-sig', low_memory=False)


def process_vi_company() -> None:
    files = list((RAW / 'vi_company').rglob('*.csv'))
    if not files:
        print('[SKIP] Missing Vietnamese company dataset')
        return
    df = pd.concat((read_file(f) for f in files), ignore_index=True)
    if not {'Content', 'Label'}.issubset(df.columns):
        raise ValueError(f'VI company schema changed: {list(df.columns)}')
    df['text'] = df['Content'].map(clean_text)
    df['ticker_candidate'] = df['Label'].fillna('').astype(str).str.strip().str.upper()
    df = df[df['text'].str.len() > 0].copy().reset_index(drop=True)
    df['text_hash'] = df['text'].map(sha)
    df['source_id'] = ['vi_company_' + str(i) for i in range(len(df))]
    suspicious = {'ROA', 'ROE', 'NIM', 'MOU', 'EPS', 'GDP', 'CPI', 'NAV', 'CEO'}
    df['tag_needs_review'] = df['ticker_candidate'].isin(suspicious)
    df['tag_verified'] = False
    save(df[['source_id', 'text', 'ticker_candidate', 'tag_needs_review',
             'tag_verified', 'text_hash']], 'vi_company_candidates.csv')
    unique = df.drop_duplicates('text_hash').copy()
    unique['language'] = 'vi'
    unique['source_dataset'] = 'vietnam_finance_news_company_tagged'
    save(unique[['source_id', 'source_dataset', 'language', 'text', 'text_hash']],
         'vi_company_dapt_candidates.csv')
    save(df[df['tag_needs_review']][['source_id', 'ticker_candidate', 'text']],
         'vi_company_suspicious_tags.csv')
    SUMMARY['vi_company'] = {'input_rows': int(len(df)), 'unique_texts': int(len(unique)),
                             'suspect_tag_rows': int(df['tag_needs_review'].sum()),
                             'warning': 'Tag is NOT verified company identity; DAPT text is NOT yet test-decontaminated.'}


def process_sentfin() -> None:
    src = RAW / 'en_sentfin' / 'SEntFiN.csv'
    if not src.exists():
        print('[SKIP] Missing SEntFiN')
        return
    df = read_file(src)
    expected = {'Title', 'Decisions'}
    if not expected.issubset(df.columns):
        raise ValueError(f'SEntFiN schema changed: {list(df.columns)}')
    rows, problems = [], []
    for idx, item in df.iterrows():
        text = clean_text(item['Title'])
        if not text:
            continue
        try:
            decisions = ast.literal_eval(str(item['Decisions']))
            if not isinstance(decisions, dict):
                raise ValueError('Decisions is not a dictionary')
        except (SyntaxError, ValueError) as exc:
            problems.append({'original_row': int(idx), 'reason': str(exc)})
            continue
        for ent, raw_sent in decisions.items():
            target = clean_text(ent)
            sent = clean_text(raw_sent).lower()
            if not target or sent not in {'negative','neutral','positive'}:
                problems.append({'original_row': int(idx), 'reason': 'Unexpected target/sentiment'})
                continue
            rows.append({'source_id': 'sentfin_' + str(idx), 'language': 'en',
                         'text': text, 'target': target, 'sentiment': sent,
                         'text_hash': sha(text), 'label_level': 'entity_sentiment',
                         'aspect': '', 'gold_vi': False})
    out = pd.DataFrame(rows, columns=['source_id','language','text','target','sentiment',
                                      'text_hash','label_level','aspect','gold_vi'])
    save(out, 'en_sentfin_entity_sentiment.csv')
    (PROC / 'sentfin_parse_errors.json').write_text(
        json.dumps(problems, ensure_ascii=False, indent=2), encoding='utf-8')
    SUMMARY['sentfin'] = {'headline_rows': int(len(df)), 'entity_label_rows': len(rows),
                           'parse_warnings': len(problems),
                           'warning': 'SEntFiN is entity sentiment, NOT aspect sentiment.'}


def process_thai() -> None:
    src = RAW / 'th_finance' / '56-1dataset_50.csv'
    if not src.exists():
        print('[SKIP] Missing Thai data')
        return
    df = read_file(src)
    expected = {'firm', 'year', 'section', 'paragraph', 'aspect', 'sentiment'}
    if not expected.issubset(df.columns):
        raise ValueError(f'Thai schema changed: {list(df.columns)}')
    out = pd.DataFrame({
        'source_id': ['thai_' + str(i) for i in range(len(df))],
        'language': 'th',
        'text': df['paragraph'].map(clean_text),
        'firm_raw': df['firm'].fillna('').map(clean_text),
        'year_raw': df['year'].fillna('').map(clean_text),
        'section_raw': df['section'].fillna('').map(clean_text),
        'aspect_raw': df['aspect'].fillna('').map(clean_text),
        'sentiment_raw': df['sentiment'].fillna('').map(clean_text),
    })
    out['text_hash'] = out['text'].map(sha)
    out = out[out['text'].str.len() > 0]
    save(out, 'th_finance_aspect_original.csv')
    SUMMARY['thai'] = {
        'rows': int(len(out)),
        'aspect_examples': out['aspect_raw'].value_counts().head(16).to_dict(),
        'sentiment_raw_values': out['sentiment_raw'].value_counts().head(15).to_dict(),
        'warning': 'Do not force-map Thai 16-category taxonomy to 5 VI aspects without reviewing cases.'
    }


def process_vi_sentiment() -> None:
    folder = RAW / 'vi_sentiment'
    if not folder.exists():
        return
    file_stats = {}
    for src in sorted(folder.rglob('*.csv')):
        df = read_file(src)
        if not {'text','sentiment'}.issubset(df.columns):
            print('[WARN] Unexpected VI sentiment CSV:', src.name, list(df.columns))
            continue
        out = pd.DataFrame({'source_id': [src.stem + '_' + str(i) for i in range(len(df))],
                            'original_split': src.stem,
                            'text': df['text'].map(clean_text),
                            'sentiment_raw': df['sentiment'].fillna(''),
                            'label_mapping_verified': False})
        out['text_hash'] = out['text'].map(sha)
        save(out, f'vi_sentiment_{src.stem}_unverified.csv')
        file_stats[src.name] = {'rows': int(len(out)),
                                'duplicates': int(out.duplicated('text_hash').sum()),
                                'sentiment_codes': out['sentiment_raw'].value_counts().to_dict()}
    if file_stats:
        SUMMARY['vi_general_sentiment'] = file_stats


def process_silver() -> None:
    src = ROOT / 'data' / 'silver' / 'phobert_dataset.csv'
    if not src.exists():
        print('[INFO] Silver file not found; skip silver audit.')
        return
    df = read_file(src)
    expected = {'ticker', 'content','business_score','leadership_score','macro_score',
                'capital_score','esg_score'}
    if not expected.issubset(df.columns):
        raise ValueError(f'Local Silver schema changed: {list(df.columns)}')
    df['text_hash'] = df['content'].map(sha)
    df['ticker_norm'] = df['ticker'].fillna('').str.upper().str.strip()
    dup = df.duplicated(['ticker_norm','text_hash'], keep=False)
    conflict_groups = []
    for key, group in df[dup].groupby(['ticker_norm', 'text_hash']):
        vals = group['label'].fillna('').unique().tolist() if 'label' in group else []
        if len(vals) > 1:
            conflict_groups.append({'ticker': key[0], 'text_hash': key[1],
                                    'labels': vals, 'n_rows': len(group)})
    (PROC / 'silver_conflicting_groups.json').write_text(
        json.dumps(conflict_groups, ensure_ascii=False, indent=2), encoding='utf-8')
    SUMMARY['vi_silver'] = {'rows': int(len(df)), 'unique_ticker_text_pairs': int(
        df[['ticker_norm', 'text_hash']].drop_duplicates().shape[0]),
        'groups_conflicting_overall_label': len(conflict_groups),
        'warning': 'LLM score=0 is NOT evidence of neutral/absent. No Silver rows become Gold automatically.'}


def check_cross_source_overlap() -> None:
    # Exact normalized hashes only; semantic near-duplicates still need manual review.
    groups: dict[str, set[str]] = {}
    vi = PROC / 'vi_company_dapt_candidates.csv'
    if vi.exists():
        groups['company_vi'] = set(pd.read_csv(vi, dtype=str)['text_hash'].dropna())
    silver = ROOT / 'data' / 'silver' / 'phobert_dataset.csv'
    if silver.exists():
        df = read_file(silver)
        if 'content' in df:
            groups['silver_vi'] = set(df['content'].fillna('').map(sha))
    sentiment_sources = sorted(PROC.glob('vi_sentiment_*_unverified.csv'))
    for src in sentiment_sources:
        data = pd.read_csv(src, dtype=str)
        groups[src.stem] = set(data['text_hash'].dropna())
    results = {}
    keys = sorted(groups)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            results[a + '__vs__' + b] = len(groups[a] & groups[b])
    if results:
        SUMMARY['cross_source_exact_overlap'] = {
            'counts': results,
            'warning': 'Only exact-normalized duplicates counted. Near-duplicate events may cross sources/splits.'}


def main() -> None:
    process_vi_company()
    process_sentfin()
    process_thai()
    process_vi_sentiment()
    process_silver()
    check_cross_source_overlap()
    target = PROC / 'audit_summary.json'
    target.write_text(json.dumps(SUMMARY, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\nAUDIT SUMMARY')
    print(json.dumps(SUMMARY, ensure_ascii=False, indent=2))
    print('\nSTEP 3 OK: review JSON audit before training.')


if __name__ == '__main__':
    main()
