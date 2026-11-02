"""Fixed-mask MLM evaluation for XLM-R Base and DAPT LoRA."""
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / ".hf_cache"))

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM

BASE = "FacebookAI/xlm-roberta-base"

p = argparse.ArgumentParser()
p.add_argument("--adapter", default=None)
p.add_argument("--max-chunks", type=int, default=64)
p.add_argument("--seed", type=int, default=3003)
args = p.parse_args()

data = pd.read_csv(
    ROOT / "data/processed/stage_A/validation_documents.csv",
    dtype=str
)

tokenizer = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForMaskedLM.from_pretrained(
    BASE, use_safetensors=True
)

if args.adapter:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, args.adapter)

model.to("cuda").eval()

loss_sum = 0.0
correct = 0
masked_total = 0
chunks = 0

with torch.inference_mode():
    for text in data["text"].dropna():
        encoded = tokenizer(
            text,
            truncation=True,
            max_length=128,
            return_overflowing_tokens=True
        )

        for original in encoded["input_ids"]:
            if args.max_chunks and chunks >= args.max_chunks:
                break

            gen = torch.Generator().manual_seed(
                args.seed + chunks
            )

            ids = list(original)
            labels = [-100] * len(ids)

            special = tokenizer.get_special_tokens_mask(
                ids, already_has_special_tokens=True
            )
            candidates = [
                i for i, flag in enumerate(special)
                if not flag
            ]

            if not candidates:
                continue

            selected = [
                i for i in candidates
                if torch.rand((), generator=gen).item() < 0.15
            ]
            if not selected:
                selected = [candidates[
                    int(torch.randint(
                        len(candidates), (1,), generator=gen
                    ).item())
                ]]

            for i in selected:
                labels[i] = original[i]
                r = torch.rand((), generator=gen).item()
                if r < 0.8:
                    ids[i] = tokenizer.mask_token_id
                elif r < 0.9:
                    ids[i] = int(torch.randint(
                        len(tokenizer), (1,), generator=gen
                    ).item())

            x = torch.tensor([ids], device="cuda")
            y = torch.tensor([labels], device="cuda")

            with torch.autocast(
                "cuda", dtype=torch.bfloat16,
                enabled=torch.cuda.is_bf16_supported()
            ):
                output = model(input_ids=x, labels=y)

            count = len(selected)
            loss_sum += output.loss.item() * count
            predicted = output.logits[0, selected].argmax(-1)
            correct += int(
                (predicted == y[0, selected]).sum().item()
            )
            masked_total += count
            chunks += 1

        if args.max_chunks and chunks >= args.max_chunks:
            break

print("Model:", args.adapter or "XLM-R BASE")
print("Seed:", args.seed)
print("Evaluated chunks:", chunks)
print("Masked tokens:", masked_total)
print("Fixed-mask MLM Loss:", round(loss_sum / masked_total, 6))
print("Masked Token Accuracy:", round(correct / masked_total, 6))
print("FIXED MLM EVALUATION: PASS")
