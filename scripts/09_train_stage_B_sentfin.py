"""Stage B — target-conditioned English financial entity sentiment (SEntFiN).

Two controlled arms:
  E0: XLM-R base + fresh LoRA(query,value) + trainable 3-class head
  E1: XLM-R base + verified Stage-A DAPT-1200 LoRA + same head

Python 3.11, torch 2.6, transformers 4.56.1, peft 0.17.1, datasets 3.6.

Run from repository root:
  python scripts/09_train_stage_B_sentfin.py --arm E1 --mode smoke
  python scripts/09_train_stage_B_sentfin.py --arm E0 --mode smoke
  python scripts/09_train_stage_B_sentfin.py --arm E0 --mode train --max-steps 600
  python scripts/09_train_stage_B_sentfin.py --arm E1 --mode train --max-steps 600

This script NEVER reads Stage B test data; test evaluation must be a separate,
locked, one-time procedure after choosing the training protocol.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HOME', str(ROOT / '.hf_cache'))
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')

MODEL_ID = 'FacebookAI/xlm-roberta-base'
SPLIT_DIR = ROOT / 'data/processed/stage_B/split_v2'
ADAPTER_A = (ROOT / 'experiments/stage_A_xlmr_lora_mlm_extension/'
             'continue_800_lr3e5/adapter_A')
OUTPUT_ROOT = ROOT / 'experiments/stage_B_sentfin_entity_sentiment'
LABELS = ('negative', 'neutral', 'positive')
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}


def sha256_file(path: Path) -> str:
    with path.open('rb') as stream:
        h = hashlib.sha256()
        for piece in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(piece)
    return h.hexdigest()


def load_split_data():
    import pandas as pd

    frames = {}
    paths = {}
    required = {'text', 'target', 'sentiment', 'text_hash',
                'leakage_group', 'source_id'}
    # Intentionally do not open the test split here.
    for name in ('train', 'validation'):
        path = SPLIT_DIR / f'sentfin_{name}.csv'
        if not path.is_file():
            raise FileNotFoundError(path)
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        if not required.issubset(df.columns):
            raise ValueError(f'{name}: columns missing {required - set(df.columns)}')
        if not len(df):
            raise ValueError(f'{name}: empty split')
        if not df['sentiment'].isin(LABEL_TO_ID).all():
            raise ValueError(f'{name}: unexpected sentiment label')
        if (df['text'].str.strip().eq('') | df['target'].str.strip().eq('')).any():
            raise ValueError(f'{name}: empty text or target')
        if df.duplicated(['text_hash', 'target', 'sentiment']).any():
            raise ValueError(f'{name}: duplicate text-target-sentiment')
        # Catch source target corruption, e.g. 'neutralings' instead of Holdings.
        not_in_text = [
            (target.casefold() not in text.casefold())
            for text, target in zip(df['text'], df['target'])
        ]
        if any(not_in_text):
            raise ValueError(f'{name}: {sum(not_in_text)} targets not in headline; '
                             'check the repaired SEntFiN split_v2')
        frames[name] = df
        paths[name] = path

    for key in ('text_hash', 'leakage_group', 'source_id'):
        overlap = set(frames['train'][key]) & set(frames['validation'][key])
        if overlap:
            raise ValueError(f'Cross-split {key}: {len(overlap)}')
    print('[DATA] train rows:', len(frames['train']),
          '| validation rows:', len(frames['validation']))
    print('[DATA] train/validation group overlaps: 0')
    return frames, {k: sha256_file(v) for k, v in paths.items()}


def normalize_adapter_key(key: str) -> str:
    return (key.replace('.lora_A.default.', '.lora_A.')
               .replace('.lora_B.default.', '.lora_B.'))


def transplant_stage_a_lora(model):
    import torch
    from safetensors.torch import load_file

    weights_file = ADAPTER_A / 'adapter_model.safetensors'
    config_file = ADAPTER_A / 'adapter_config.json'
    if not weights_file.is_file() or not config_file.is_file():
        raise FileNotFoundError(f'Stage A adapter missing: {ADAPTER_A}')
    config = json.loads(config_file.read_text(encoding='utf-8'))
    if config.get('base_model_name_or_path') != MODEL_ID:
        raise ValueError('Stage A base model differs from Stage B')
    if int(config['r']) != 8 or set(config['target_modules']) != {'query', 'value'}:
        raise ValueError('Unexpected Stage A LoRA architecture')

    source = load_file(str(weights_file), device='cpu')
    dest = {
        normalize_adapter_key(name): parameter
        for name, parameter in model.named_parameters()
        if '.lora_A.' in name or '.lora_B.' in name
    }
    if set(source) != set(dest):
        raise ValueError('Adapter tensors mismatch: '
                         f'missing={len(set(dest) - set(source))} '
                         f'extra={len(set(source) - set(dest))}')
    if len(source) != 48:
        raise ValueError(f'Unexpected Stage A LoRA tensor count: {len(source)}')
    with torch.no_grad():
        for name, param in dest.items():
            tensor = source[name]
            if tensor.shape != param.shape:
                raise ValueError(f'LoRA shape mismatch at {name}')
            param.copy_(tensor.to(device=param.device, dtype=param.dtype))
            if not torch.equal(param.detach().cpu(), tensor.cpu()):
                raise ValueError(f'LoRA copy verification failed at {name}')
    print('[INIT] DAPT-1200 LoRA transferred:', len(source), 'tensors')
    return sha256_file(weights_file)


def build_model(arm: str):
    from transformers import AutoModelForSequenceClassification
    from peft import LoraConfig, get_peft_model

    base = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID,
        num_labels=len(LABELS),
        id2label={i: label for i, label in enumerate(LABELS)},
        label2id=LABEL_TO_ID,
        use_safetensors=True,
    )
    model = get_peft_model(
        base,
        LoraConfig(
            task_type='SEQ_CLS',
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            target_modules=['query', 'value'],
            bias='none',
            modules_to_save=['classifier'],
        ),
    )
    adapter_hash = None
    if arm == 'E1':
        adapter_hash = transplant_stage_a_lora(model)
    else:
        print('[INIT] E0 fresh LoRA (no Stage A weights)')

    if hasattr(model, 'enable_input_require_grads'):
        model.enable_input_require_grads()
    trainable = [n for n, p in model.named_parameters() if p.requires_grad]
    if not any('classifier' in n for n in trainable):
        raise ValueError('Classifier head is not trainable')
    if not any('lora_A' in n or 'lora_B' in n for n in trainable):
        raise ValueError('LoRA matrices are not trainable')
    model.print_trainable_parameters()
    return model, adapter_hash


def calculate_metrics(predictions):
    """No scikit-learn dependency; sklearn-compatible per-class F1 convention."""
    import numpy as np

    logits = predictions.predictions
    if isinstance(logits, tuple):
        logits = logits[0]
    y_pred = np.asarray(logits).argmax(axis=-1)
    y_true = np.asarray(predictions.label_ids).reshape(-1)
    f1 = []
    result = {'accuracy': float(np.mean(y_pred == y_true))}
    for index, name in enumerate(LABELS):
        tp = int(np.sum((y_true == index) & (y_pred == index)))
        fp = int(np.sum((y_true != index) & (y_pred == index)))
        fn = int(np.sum((y_true == index) & (y_pred != index)))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        this_f1 = (2 * precision * recall / (precision + recall)
                   if precision + recall else 0.0)
        f1.append(this_f1)
        result[f'f1_{name}'] = this_f1
    result['macro_f1'] = float(np.mean(f1))
    return result


def run(args):
    import numpy as np
    import torch
    from datasets import Dataset
    from transformers import (
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; do not run expensive Stage B on CPU')
    set_seed(args.seed)

    frames, split_sha = load_split_data()
    if args.mode == 'smoke':
        frames = {
            'train': frames['train'].head(128).copy(),
            'validation': frames['validation'].head(96).copy(),
        }
        print('[SMOKE] subset: 128 train / 96 validation; TEST NOT READ')

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    datasets = {}
    for name, frame in frames.items():
        docs = Dataset.from_dict({
            'text': frame['text'].tolist(),
            'target': frame['target'].tolist(),
            'labels': [LABEL_TO_ID[label] for label in frame['sentiment']],
        })

        def tokenize(batch):
            return tokenizer(
                batch['text'],
                text_pair=batch['target'],
                truncation=True,
                max_length=args.max_length,
            )

        datasets[name] = docs.map(
            tokenize, batched=True, batch_size=128,
            remove_columns=['text', 'target'],
            desc=f'Tokenize {name} (headline + target pair)',
        )

    model, adapter_sha = build_model(args.arm)
    model.config.use_cache = False

    max_steps = 5 if args.mode == 'smoke' else args.max_steps
    interval = 5 if args.mode == 'smoke' else args.eval_steps
    run_dir = OUTPUT_ROOT / args.arm.lower() / args.mode
    run_dir.mkdir(parents=True, exist_ok=True)

    bf16 = bool(torch.cuda.is_bf16_supported())
    train_args = TrainingArguments(
        output_dir=str(run_dir / 'trainer_checkpoints'),
        overwrite_output_dir=False,
        max_steps=max_steps,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=4,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={'use_reentrant': False},
        learning_rate=args.learning_rate,
        lr_scheduler_type='linear',
        warmup_ratio=0.06,
        weight_decay=0.01,
        optim='adamw_torch',
        bf16=bf16,
        fp16=not bf16,
        dataloader_num_workers=0,
        dataloader_pin_memory=True,
        logging_strategy='steps',
        logging_steps=1 if args.mode == 'smoke' else 20,
        eval_strategy='steps',
        eval_steps=interval,
        save_strategy='steps',
        save_steps=interval,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model='macro_f1',
        greater_is_better=True,
        label_names=['labels'],
        prediction_loss_only=False,
        report_to='none',
        remove_unused_columns=True,
        seed=args.seed,
        data_seed=args.seed,
    )
    trainer = Trainer(
        model=model,
        args=train_args,
        train_dataset=datasets['train'],
        eval_dataset=datasets['validation'],
        data_collator=DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8),
        processing_class=tokenizer,
        compute_metrics=calculate_metrics,
    )
    print('[RUN]', args.arm, args.mode,
          '| steps:', max_steps,
          '| effective batch:', args.grad_accum,
          '| max length:', args.max_length,
          '| learning rate:', args.learning_rate)
    print('[SAFETY] Test split was NOT loaded')

    torch.cuda.reset_peak_memory_stats()
    trainer.train()
    metrics = trainer.evaluate()
    adapter_dir = run_dir / 'adapter_B'
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    peak = round(torch.cuda.max_memory_allocated() / (1024 ** 3), 4)

    record = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'arm': args.arm,
        'mode': args.mode,
        'model_id': MODEL_ID,
        'stage_a_adapter': str(ADAPTER_A) if args.arm == 'E1' else None,
        'stage_a_adapter_sha256': adapter_sha,
        'train_csv_sha256': split_sha['train'],
        'validation_csv_sha256': split_sha['validation'],
        'seed': args.seed,
        'training_rows': len(datasets['train']),
        'validation_rows': len(datasets['validation']),
        'test_data_used': False,
        'input': 'tokenizer(headline, text_pair=target)',
        'label_mapping': LABEL_TO_ID,
        'max_length': args.max_length,
        'gradient_accumulation_steps': args.grad_accum,
        'max_steps': max_steps,
        'learning_rate': args.learning_rate,
        'eval_steps': interval,
        'best_checkpoint': trainer.state.best_model_checkpoint,
        'best_validation_macro_f1': trainer.state.best_metric,
        'metrics': {k: float(v) for k, v in metrics.items()
                    if isinstance(v, (float, int, np.number))},
        'adapter_directory': str(adapter_dir),
        'gpu_peak_allocated_gib': peak,
    }
    (run_dir / 'run_manifest.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print('[RESULT] Validation Macro-F1:', metrics.get('eval_macro_f1'))
    print('[RESULT] Validation accuracy:', metrics.get('eval_accuracy'))
    print('[RESULT] Best checkpoint:', trainer.state.best_model_checkpoint)
    print('[RESULT] Peak VRAM GiB:', peak)
    print('[SAVED]', adapter_dir)
    print(f'STAGE B {args.arm} {args.mode.upper()}: PASS')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--arm', required=True, choices=['E0', 'E1'])
    p.add_argument('--mode', choices=['smoke', 'train'], default='smoke')
    p.add_argument('--max-steps', type=int, default=600)
    p.add_argument('--max-length', type=int, default=160)
    p.add_argument('--grad-accum', type=int, default=16)
    p.add_argument('--learning-rate', type=float, default=1e-4)
    p.add_argument('--eval-steps', type=int, default=50)
    p.add_argument('--seed', type=int, default=42)
    args = p.parse_args()
    if args.max_steps < 1 or args.grad_accum < 1 or args.eval_steps < 1:
        p.error('max-steps, grad-accum, eval-steps must be positive')
    if not 64 <= args.max_length <= 256:
        p.error('max-length must be 64–256')
    if args.learning_rate <= 0:
        p.error('learning-rate must be positive')
    if args.mode == 'train' and args.max_steps % args.eval_steps != 0:
        p.error('max-steps must be divisible by eval-steps (for checkpoint selection)')
    run(args)


if __name__ == '__main__':
    main()
