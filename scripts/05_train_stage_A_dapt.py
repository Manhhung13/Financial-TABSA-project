"""Stage A: Vietnamese financial-domain MLM adaptation of XLM-R with LoRA.

Designed for Python 3.11/3.12/3.13, Windows PowerShell, transformers 4.56.1,
peft 0.17.1, torch 2.6+cu124. Stage A does NOT train sentiment labels.

Usage:
  python scripts/05_train_stage_A_dapt.py --mode prepare
  python scripts/05_train_stage_A_dapt.py --mode smoke
  python scripts/05_train_stage_A_dapt.py --mode train --max-steps 400

The output is an encoder LoRA adapter. For Stage B it must be attached to
an XLM-R base encoder; MLM head is NOT copied to a classification task.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HOME', str(ROOT / '.hf_cache'))
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')

CORPUS_FILE = ROOT / 'data' / 'processed' / 'vi_company_dapt_candidates.csv'
OUTPUT_DATA = ROOT / 'data' / 'processed' / 'stage_A'
OUTPUT_EXPERIMENT = ROOT / 'experiments' / 'stage_A_xlmr_lora_mlm'
MODEL_ID = 'FacebookAI/xlm-roberta-base'


def clean_text(t: object) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(t).replace('\u00a0', ' '))).strip()


def text_hash(t: object) -> str:
    return hashlib.sha256(clean_text(t).casefold().encode('utf-8')).hexdigest()


def get_holdout_hashes() -> tuple[set[str], list[str]]:
    """Exclude ONLY exact-normalized matches to candidates in reviewed Gold pool.

    IMPORTANT: This is not a substitute for near-duplicate/event-level exclusion.
    """
    holdouts: set[str] = set()
    notes: list[str] = []
    for name in ('data/gold/article_pool_to_verify.csv', 'data/gold/heldout_documents.csv'):
        path = ROOT / name
        if not path.exists():
            continue
        d = pd.read_csv(path, dtype=str, encoding='utf-8-sig')
        txt_col = next((c for c in ('content', 'text', 'article_text') if c in d.columns), None)
        if txt_col:
            holdouts.update(text_hash(v) for v in d[txt_col].dropna().tolist() if clean_text(v))
            notes.append(f'{name}: read {len(d)} rows of text')
    return holdouts, notes


def prepare(seed: int, max_articles: int) -> tuple[Path, Path, dict]:
    if not CORPUS_FILE.exists():
        raise FileNotFoundError(
            f'Missing {CORPUS_FILE}\n'
            'Run the original starter kit: python scripts\\02_download_datasets.py and '
            'python scripts\\03_audit_prepare.py first.'
        )
    df = pd.read_csv(CORPUS_FILE, dtype=str, encoding='utf-8-sig')
    if 'text' not in df.columns:
        raise ValueError(f'Expected text column in {CORPUS_FILE}. Found: {list(df.columns)}')
    input_rows = len(df)
    df = df.copy()
    df['text'] = df['text'].fillna('').map(clean_text)
    df = df[df['text'].str.len() >= 40].copy()
    df['text_hash'] = df['text'].map(text_hash)
    df = df.drop_duplicates('text_hash').reset_index(drop=True)
    holdouts, holdout_notes = get_holdout_hashes()
    num_excluded = int(df['text_hash'].isin(holdouts).sum())
    df = df[~df['text_hash'].isin(holdouts)].reset_index(drop=True)
    if max_articles > 0 and len(df) > max_articles:
        df = df.sample(n=max_articles, random_state=seed).reset_index(drop=True)
    if len(df) < 20:
        raise ValueError(f'Too few unique documents after filtering: {len(df)}. Need at least 20.')
    # Conservative leakage groups from existing R3 audit candidates.
    source = pd.read_csv(
        ROOT / 'data/processed/vi_company_candidates.csv', dtype=str
    )
    raw_hash = {
        int(sid.rsplit('_', 1)[1]) + 1: h
        for sid, h in zip(source['source_id'], source['text_hash'])
    }

    parent = {h: h for h in df['text_hash']}

    if not set(parent).issubset(set(raw_hash.values())):
        raise ValueError('DAPT corpus and R3 source mapping differ')

    def find(h):
        while parent[h] != h:
            parent[h] = parent[parent[h]]
            h = parent[h]
        return h

    def join(a, b):
        if a not in parent or b not in parent:
            return
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    near_path = ROOT / 'reports/T-012_R3_near_duplicate_review_queue.json'
    exact_path = ROOT / 'reports/T-012_R3_exact_duplicate_groups.json'

    pairs = json.loads(near_path.read_text(encoding='utf-8'))
    linked_pairs = 0

    for pair in pairs:
        if pair.get('left_dataset') != 'VI_COMPANY':
            continue
        if pair.get('right_dataset') != 'VI_COMPANY':
            continue
        a = raw_hash.get(int(pair['left_row']))
        b = raw_hash.get(int(pair['right_row']))
        if a in parent and b in parent:
            join(a, b)
            linked_pairs += 1

    exact_groups = json.loads(exact_path.read_text(encoding='utf-8'))
    for item in exact_groups:
        if item.get('source_dataset') != 'VI_COMPANY':
            continue
        if item.get('match_type') != 'exact_normalized_text':
            continue
        members = [
            raw_hash.get(int(r)) for r in item['source_rows']
        ]
        for h in members[1:]:
            join(members[0], h)

    groups = {}
    for i, h in enumerate(df['text_hash']):
        groups.setdefault(find(h), []).append(i)

    components = list(groups.values())
    random.Random(seed).shuffle(components)

    target_val = max(2, int(round(len(df) * .05)))
    val_idx = []
    for component in components:
        if len(val_idx) + len(component) <= target_val:
            val_idx.extend(component)

    if len(val_idx) < 2:
        raise RuntimeError('Too few grouped validation documents')

    val_set = set(val_idx)
    train_idx = [i for i in range(len(df)) if i not in val_set]

    df['provisional_leakage_group'] = [
        find(h) for h in df['text_hash']
    ]
    cols = ['text_hash', 'text', 'provisional_leakage_group']
    train = df.iloc[train_idx][cols]
    val = df.iloc[val_idx][cols]

    overlap = (
        set(train['provisional_leakage_group'])
        & set(val['provisional_leakage_group'])
    )
    if overlap:
        raise RuntimeError('Group leakage detected')

    print('[GROUP] provisional groups:', len(groups))
    print('[GROUP] linked near-duplicate pairs:', linked_pairs)
    print('[GROUP] cross-split groups:', len(overlap))
    OUTPUT_DATA.mkdir(parents=True, exist_ok=True)
    train_file = OUTPUT_DATA / 'train_documents.csv'
    val_file = OUTPUT_DATA / 'validation_documents.csv'
    train.to_csv(train_file, index=False, encoding='utf-8-sig')
    val.to_csv(val_file, index=False, encoding='utf-8-sig')
    stats = {
        'input_rows': input_rows,
        'unique_filtered_rows': len(df),
        'train_documents': len(train),
        'mlm_validation_documents': len(val),
        'excluded_exact_gold_candidates': num_excluded,
        'holdout_source_notes': holdout_notes,
        'limitations': [
            'Gold test MUST be split by document/event and locked before final research training.',
            'Exact text hash excludes exact matches only, not semantic/event near duplicates.',
            'MLM validation loss does NOT establish better sentiment F1.',
        ],
        'seed': seed,
        'max_articles': max_articles,
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT_DATA / 'prepare_manifest.json').write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print('[DATA] original:', input_rows, '| eligible:', len(df), '| excluded Gold exact:', num_excluded)
    print('[DATA] train documents:', len(train), '| MLM validation documents:', len(val))
    if not holdout_notes:
        print('[WARNING] NO Gold/holdout text supplied. This run must NOT be reported as leakage-free.')
    print('[DATA] saved:', OUTPUT_DATA)
    return train_file, val_file, stats


def train(args: argparse.Namespace, train_file: Path, val_file: Path, stats: dict) -> None:
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (
        AutoModelForMaskedLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        default_data_collator,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is false in this .venv. Stop and diagnose before training.')
    if torch.cuda.get_device_properties(0).total_memory / (1024 ** 3) < 5:
        print('[WARNING] Below 5 GiB VRAM. This script may need additional reductions.')
    set_seed(args.seed)
    print('[GPU]', torch.cuda.get_device_name(0), 'BF16:', torch.cuda.is_bf16_supported())
    print('[MODEL]', MODEL_ID, '| max_length:', args.max_length)
    print('[RUN]', args.mode, '| optimization steps:', args.max_steps, '| epochs:', args.epochs)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    ds = load_dataset('csv', data_files={'train': str(train_file), 'validation': str(val_file)})

    def token_chunks(examples):
        enc = tokenizer(examples['text'], truncation=True,
                        max_length=args.max_length,
                        return_overflowing_tokens=True)
        # Retain overflowed chunks beyond the beginning of a long article.
        enc.pop('overflow_to_sample_mapping', None)
        return enc

    ds = ds.map(token_chunks, batched=True, batch_size=20, num_proc=1,
                remove_columns=ds['train'].column_names,
                desc='Tokenize and chunk (keep long-document tails)')
    print('[CHUNKS]', len(ds['train']), 'train; ', len(ds['validation']), 'validation')
    if len(ds['train']) < 5:
        raise RuntimeError('Too few MLM token chunks.')

    model = AutoModelForMaskedLM.from_pretrained(MODEL_ID, use_safetensors=True)
    model.config.use_cache = False
    config = LoraConfig(r=args.lora_r, lora_alpha=args.lora_alpha,
                        lora_dropout=0.05, bias='none',
                        target_modules=['query', 'value'])
    model = get_peft_model(model, config)
    # For LoRA + checkpointing, make sure gradients propagate to adapters.
    if hasattr(model, 'enable_input_require_grads'):
        model.enable_input_require_grads()
    model.print_trainable_parameters()

    OUTPUT_EXPERIMENT.mkdir(parents=True, exist_ok=True)
    run_name = 'smoke' if args.mode == 'smoke' else ('full_epoch' if args.full_epoch else 'pilot_steps')
    run_dir = OUTPUT_EXPERIMENT / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    # Fixed validation masks: same algorithm/seed as external evaluator.
    def make_fixed_mask(example, idx):
        original = list(example['input_ids'])
        ids = original.copy()
        labels = [-100] * len(ids)
        special = tokenizer.get_special_tokens_mask(
            original, already_has_special_tokens=True
        )
        candidates = [i for i, flag in enumerate(special) if not flag]
        if not candidates:
            raise ValueError('Validation chunk has no maskable tokens')

        gen = torch.Generator().manual_seed(3003 + idx)
        selected = [
            i for i in candidates
            if torch.rand((), generator=gen).item() < 0.15
        ]
        if not selected:
            selected = [candidates[int(torch.randint(
                len(candidates), (1,), generator=gen
            ).item())]]

        for i in selected:
            labels[i] = original[i]
            r = torch.rand((), generator=gen).item()
            if r < 0.8:
                ids[i] = tokenizer.mask_token_id
            elif r < 0.9:
                ids[i] = int(torch.randint(
                    len(tokenizer), (1,), generator=gen
                ).item())

        return {'input_ids': ids, 'labels': labels}

    fixed_eval = ds['validation'].map(
        make_fixed_mask, with_indices=True,
        desc='Prepare deterministic MLM validation'
    )

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer,
                                               mlm=True, mlm_probability=0.15)
    def split_collator(features):
        if 'labels' in features[0]:
            return default_data_collator(features)
        return collator(features)

    bf16 = bool(torch.cuda.is_bf16_supported())
    scheduling_steps = args.max_steps if args.max_steps > 0 else 200
    train_args = TrainingArguments(
        output_dir=str(run_dir / 'trainer_checkpoints'),
        max_steps=args.max_steps,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={'use_reentrant': False},
        learning_rate=args.learning_rate,
        lr_scheduler_type='linear',
        warmup_ratio=0.05,
        weight_decay=0.01,
        optim='adamw_torch',
        bf16=bf16,
        fp16=not bf16,
        dataloader_num_workers=0,
        dataloader_pin_memory=True,
        logging_strategy='steps',
        logging_steps=max(1, min(10, scheduling_steps)),
        eval_strategy='steps',
        eval_steps=max(1, min(50, scheduling_steps)),
        save_strategy='no' if args.mode == 'smoke' else 'steps',
        save_steps=max(1, min(50, scheduling_steps)),
        save_total_limit=2,
        load_best_model_at_end=(args.mode != 'smoke'),
        metric_for_best_model='eval_loss',
        greater_is_better=False,
        prediction_loss_only=True,
        report_to='none',
        remove_unused_columns=True,
        seed=args.seed,
        data_seed=args.seed,
    )
    trainer = Trainer(model=model, args=train_args,
                      train_dataset=ds['train'], eval_dataset=fixed_eval,
                      data_collator=split_collator, processing_class=tokenizer)
    torch.cuda.reset_peak_memory_stats()
    trainer.train()
    metrics = trainer.evaluate()
    adapter_dir = run_dir / 'adapter_A'
    trainer.model.save_pretrained(str(adapter_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(adapter_dir))
    peak = round(torch.cuda.max_memory_allocated() / (1024 ** 3), 3)
    record = {
        **stats, 'model_id': MODEL_ID, 'mode': args.mode,
        'architecture': 'XLMRobertaForMaskedLM + LoRA(query,value)',
        'task': 'masked_language_modeling',
        'vram_peak_allocated_gib': peak,
        'max_steps_configuration': args.max_steps,
        'epochs_configuration': args.epochs,
        'is_full_epoch': args.full_epoch,
        'max_length': args.max_length,
        'effective_batch': args.grad_accum,
        'learning_rate': args.learning_rate,
        'metrics': {k: float(v) for k, v in metrics.items()
                    if isinstance(v, (float, int))},
        'adapter_directory': str(adapter_dir),
        'fixed_eval_seed': 3003,
        'best_checkpoint': trainer.state.best_model_checkpoint,
        'best_eval_loss': trainer.state.best_metric,
        'what_next': 'Use Stage A encoder adapter for Stage B task-specific sentiment head.',
    }
    (run_dir / 'run_manifest.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[RESULT] MLM eval_loss:', metrics.get('eval_loss'))
    print('[RESULT] Peak GPU allocated GiB:', peak)
    print('[SAVED]', adapter_dir)
    print('STAGE A OK:', args.mode, '| saved LoRA adapter for an XLM-R encoder.')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['prepare', 'smoke', 'train'], default='prepare')
    p.add_argument('--full-epoch', action='store_true', help='Train over all token chunks for --epochs; ignores max_steps.')
    p.add_argument('--epochs', type=float, default=1.0, help='Only used with --full-epoch.')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--max-articles', type=int, default=0,
                   help='Limit documents (smoke defaults to 250). Zero = all.')
    p.add_argument('--max-steps', type=int, default=0,
                   help='Smoke defaults to 5; train defaults to 400.')
    p.add_argument('--max-length', type=int, default=128)
    p.add_argument('--grad-accum', type=int, default=16)
    p.add_argument('--learning-rate', type=float, default=1e-4)
    p.add_argument('--lora-r', type=int, default=8)
    p.add_argument('--lora-alpha', type=int, default=16)
    args = p.parse_args()
    if args.max_length < 64 or args.max_length > 256:
        p.error('--max-length must be from 64 to 256 for this RTX4050 runbook.')
    if args.max_steps < 0 or args.max_articles < 0 or args.grad_accum < 1 or args.epochs <= 0:
        p.error('max-steps/max-articles must be >= 0; grad-accum >=1')
    if args.mode == 'smoke':
        args.max_steps = args.max_steps or 5
        args.max_articles = args.max_articles or 250
    if args.mode == 'train':
        args.max_steps = -1 if args.full_epoch else (args.max_steps or 400)
        if not (ROOT / 'data' / 'gold' / 'article_pool_to_verify.csv').exists() and not (
                ROOT / 'data' / 'gold' / 'heldout_documents.csv').exists():
            print('[WARNING] Gold will be independently collected later.')
            print('[WARNING] Verify event overlap before future Gold Test evaluation.')
    train_file, val_file, stats = prepare(args.seed, args.max_articles)
    if args.mode != 'prepare':
        train(args, train_file, val_file, stats)
    else:
        print('STAGE A PREPARE OK. No model training in prepare mode.')


if __name__ == '__main__':
    main()
