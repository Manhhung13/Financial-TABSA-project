"""Step 4: Create BLANK human-annotation templates; never auto-generate Gold labels.

Publication timestamps are OPTIONAL for the eventual group-safe Gold split.
The emitted group_id is a provisional text hash, not an adjudicated event cluster.
This script does NOT perform a Gold train/val/test split or pass T-003B gates.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import random
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / 'data' / 'gold'
GOLD.mkdir(parents=True, exist_ok=True)
ASPECTS = ['business_financials','leadership_insider','macro_policy',
           'capital_structure','legal_esg']
SCORE_MAP = {'business_financials':'business_score',
             'leadership_insider':'leadership_score',
             'macro_policy':'macro_score',
             'capital_structure':'capital_score',
             'legal_esg':'esg_score'}


def text_hash(s: str) -> str:
    s = unicodedata.normalize('NFC', s)
    s = re.sub(r'\s+', ' ', s).strip().casefold()
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def from_silver(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    required = {'ticker','content'} | set(SCORE_MAP.values())
    if not required.issubset(df.columns):
        raise ValueError(f'Unexpected Silver columns: {list(df.columns)}')
    df = df.copy()
    df['ticker'] = df['ticker'].fillna('').astype(str).str.strip().str.upper()
    df['content'] = df['content'].fillna('').astype(str).str.strip()
    df = df[(df['ticker'] != '') & (df['content'] != '')].copy()
    df['text_hash'] = df['content'].map(text_hash)
    df = df.drop_duplicates(['ticker', 'text_hash']).reset_index(drop=True)
    df['source_id'] = ['silver_' + str(i) for i in range(len(df))]
    rng = random.Random(seed)
    selected: list[int] = []
    quota = max(1, math.ceil(n * 0.12))
    # LLM scores are only used for sampling candidate cases, not as Gold labels.
    for aspect in ['legal_esg','macro_policy','leadership_insider','capital_structure','business_financials']:
        values = pd.to_numeric(df[SCORE_MAP[aspect]], errors='coerce').fillna(0)
        available = [i for i in df.index[values != 0] if i not in selected]
        rng.shuffle(available)
        selected += available[:min(quota, n-len(selected))]
    remaining = [i for i in df.index if i not in selected]
    rng.shuffle(remaining)
    selected += remaining[:max(0, n-len(selected))]
    return df.loc[selected[:n], ['source_id','ticker','content','text_hash']].copy()


def from_company(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    required = {'source_id','ticker_candidate','text','text_hash'}
    if not required.issubset(df.columns):
        raise ValueError('Company candidates are missing expected columns.')
    df = df.copy()
    df = df[(df['ticker_candidate'].fillna('') != '') &
            (df['text'].fillna('') != '') &
            (~df['tag_needs_review'].astype(str).str.lower().eq('true'))]
    df = df.drop_duplicates(['ticker_candidate','text_hash'])
    if len(df) > n:
        df = df.sample(n=n, random_state=seed)
    return df.rename(columns={'ticker_candidate':'ticker', 'text':'content'})[
        ['source_id','ticker','content','text_hash']].copy()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=100, help='Number of article-target units, not rows')
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()
    silver = ROOT / 'data' / 'silver' / 'phobert_dataset.csv'
    company = ROOT / 'data' / 'processed' / 'vi_company_candidates.csv'
    if args.n <= 0:
        raise ValueError('--n must be positive.')
    if silver.exists():
        df = from_silver(pd.read_csv(silver, dtype=str, encoding='utf-8-sig'), args.n, args.seed)
        origin = 'llm_silver_candidate'
        print('Selected from local Silver CSV; NO score copied as Gold.')
    elif company.exists():
        df = from_company(pd.read_csv(company, dtype=str, encoding='utf-8-sig'), args.n, args.seed)
        origin = 'company_tag_candidate'
        print('Selected from company-tagged corpus; ticker must be verified.')
    else:
        raise FileNotFoundError('Run Step 3, or place phobert_dataset.csv in data/silver/.')
    df = df.reset_index(drop=True)
    df['group_id'] = df['text_hash']
    df['sample_id'] = [f'VN_REVIEW_{i+1:04d}' for i in range(len(df))]
    df['source_type'] = origin
    df['source_url'] = ''
    df['published_at'] = ''
    source_pool = GOLD / 'article_pool_to_verify.csv'
    df[['sample_id','group_id','source_type','source_id','ticker','content',
        'source_url','published_at']].to_csv(source_pool,index=False,encoding='utf-8-sig')
    rows = []
    for item in df.itertuples(index=False):
        for aspect in ASPECTS:
            rows.append({'sample_id':item.sample_id, 'group_id':item.group_id,
                         'source_id':item.source_id, 'ticker_candidate':item.ticker,
                         'aspect':aspect, 'aspect_present':'', 'sentiment':'',
                         'evidence':'', 'annotation_status':'pending',
                         'annotator_id':'', 'notes':''})
    template = pd.DataFrame(rows)
    path = GOLD / 'gold_annotation_template.csv'
    template.to_csv(path,index=False,encoding='utf-8-sig')
    print('Article pool:', source_pool, 'items:', len(df))
    print('Blank annotation template:', path, 'rows:', len(template))
    print('STEP 4 OK: this is NOT yet a Gold dataset.')
    print('published_at is OPTIONAL for Gold; group_id is only a provisional text hash.')
    print('Verify source rights, company identity and event grouping before grouped split/seal.')
    print('Annotate aspect_present as yes/no; sentiment as negative/neutral/positive only if yes.')
    print('Use article_pool_to_verify.csv to verify the original source and find evidence.')
    print('Uncertain, mixed, unclear ticker -> annotation_status=needs_review; do not force a label.')


if __name__ == '__main__':
    main()
