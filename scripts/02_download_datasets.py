"""Step 2: Download 3 source datasets. Optionally download general VI sentiment.

The original files are preserved unmodified; source SHA/URL/hashes are recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HOME', str(ROOT / '.hf_cache'))

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from huggingface_hub import HfApi, hf_hub_download


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def hf_csv(repo: str, folder: str, preferred: str | None = None) -> list[dict]:
    out = ROOT / 'data' / 'raw' / folder
    out.mkdir(parents=True, exist_ok=True)
    api = HfApi()
    info = api.dataset_info(repo)
    revision = info.sha
    paths = sorted(p for p in api.list_repo_files(repo, repo_type='dataset', revision=revision)
                   if p.lower().endswith('.csv'))
    if preferred:
        matches = [p for p in paths if Path(p).name.lower() == preferred.lower()]
        if not matches:
            raise RuntimeError(f'Expected {preferred} in {repo}; CSV files: {paths}')
        paths = matches
    if not paths:
        raise RuntimeError(f'No CSV files in {repo}. Repo files: {paths}')
    result = []
    for remote_filename in paths:
        print('Downloading HF:', repo, remote_filename)
        cached = hf_hub_download(repo_id=repo, repo_type='dataset',
                                 filename=remote_filename, revision=revision)
        local = out / Path(remote_filename).name
        shutil.copyfile(cached, local)
        result.append({'source': repo, 'revision': revision, 'remote_file': remote_filename,
                       'local_file': str(local.relative_to(ROOT)), 'bytes': local.stat().st_size,
                       'sha256': digest(local)})
    return result


def github_file(url: str, folder: str, filename: str) -> dict:
    out = ROOT / 'data' / 'raw' / folder
    out.mkdir(parents=True, exist_ok=True)
    target = out / filename
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5,
                  status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retry))
    print('Downloading GitHub:', url)
    with session.get(url, stream=True, timeout=(20, 120)) as response:
        response.raise_for_status()
        with target.with_suffix(target.suffix + '.part').open('wb') as fout:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    fout.write(chunk)
    target.with_suffix(target.suffix + '.part').replace(target)
    if target.stat().st_size < 100:
        raise RuntimeError(f'Suspiciously small download: {target}')
    return {'source': url, 'revision': 'main (recorded source URL and content hash)',
            'remote_file': filename, 'local_file': str(target.relative_to(ROOT)),
            'bytes': target.stat().st_size, 'sha256': digest(target)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--include-vi-sentiment', action='store_true',
                    help='Also download the 3,692-row general Vietnamese sentiment dataset.')
    args = ap.parse_args()
    manifest = {'downloaded_at_utc': datetime.now(timezone.utc).isoformat(), 'files': []}
    tasks = [
        ('VI company-tagged', lambda: hf_csv('duongnghia222/vietnam_finance_news_company_tagged',
                                            'vi_company', preferred=None)),
        ('SEntFiN', lambda: [github_file(
            'https://raw.githubusercontent.com/pyRis/SEntFiN/main/SEntFiN.csv',
            'en_sentfin', 'SEntFiN.csv')]),
        ('Thai Financial Aspect Sentiment', lambda: [github_file(
            'https://raw.githubusercontent.com/nlp-chula/finnlp-sentiment/main/56-1dataset_50.csv',
            'th_finance', '56-1dataset_50.csv')]),
    ]
    if args.include_vi_sentiment:
        tasks.append(('VI general sentiment', lambda: hf_csv(
            'duong2110/finance-sentiment-vietnamese', 'vi_sentiment', preferred=None)))
    for title, fn in tasks:
        try:
            records = fn()
            manifest['files'].extend(records)
            print('[OK]', title, 'files:', len(records))
        except Exception as exc:
            print('[FAILED]', title, type(exc).__name__, str(exc))
            manifest.setdefault('errors', []).append({'dataset': title, 'reason': str(exc)})
    target = ROOT / 'data' / 'raw' / 'download_manifest.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Manifest:', target)
    print('Downloaded:', len(manifest['files']), 'files; errors:', len(manifest.get('errors', [])))
    if manifest.get('errors'):
        raise SystemExit('At least one download failed. Resolve before Step 3.')


if __name__ == '__main__':
    main()
