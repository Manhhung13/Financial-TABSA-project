# Training architecture: XLM-R sequential adaptation

## Desired inference
`(context, ticker, aspect)` -> presence head (binary) and conditional sentiment head (3-way). Encode context and short query as a text pair. Prefer target-centered windows within max token budget; preserve numbers, negations and evidence.

## Stage A - VI DAPT / MLM
Input: nonlabelled clean Vietnamese financial texts (no Gold test overlap). `AutoModelForMaskedLM`, dynamic masking ~15%; save encoder/LoRA + tokenizer + corpus manifest + MLM val loss. MLM loss alone does NOT establish target-task improvement.

## Stage B - EN SEntFiN
One row per labeled entity in each headline. Input `(headline, target_entity)`, labels NEG/NEU/POS. New entity sentiment classification head, CE loss. Keep all entity rows from one headline together in train/val split.

## Stage C - TH financial aspect + polarity
Validate actual Thai row granularity: one vs multiple aspect labels; do not silently collapse multi-label rows. Use 16-class aspect head + 3-class sentiment head only IF dataset supports that shape; otherwise appropriate multi-label/masked loss. Thai `firm` is source report entity, not a guaranteed target in every sentence.

## Stage D - VI Gold TABSA
For each human-verified target/aspect sample: binary presence head + three-class sentiment head, with sentiment loss masked when no trustworthy label/presence. Save tokenizer, encoder/adapter, heads, mapping, thresholds selected only on val, model card, experiment manifest.

Loss (conceptual): L = CE_presence(valid labels) + lambda * masked_CE_sentiment(valid, present). Absence is not neutral. Source/aux tasks use own head and losses.

## Critical adapter transition contract
Stage-specific architectures change (MLM -> sequence classifier -> Thai heads -> target-aspect heads). Do NOT merely load adapter_A into a differently named module and assume it worked. For each transition prove: (1) base checkpoint/revision identical, (2) LoRA target layer names and shapes compatible, (3) expected adapter tensors loaded, no unexpected/missing trainable keys beyond documented head, (4) initial predictions and checksum recorded. If incompatibility occurs: implement a reviewed encoder/adapter remapping or merge with documented memory costs; do not silently restart from fresh base.

## Low-VRAM envelope
RTX 4050 6GB: prefer XLM-R base, PEFT LoRA r=8 alpha=16, BF16 where supported, per-device batch=1, grad accumulation=16, sequence length=128 initial, dataloader_workers=0 on Windows. First run one forward/backward smoke; record VRAM. DAPT may require alternate/remote GPU; do not claim full fine-tune feasible without measuring.

## Scientific constraints
No promised best model. Compare baseline Gold-only vs A-only, B-only, C-only and combined path with fixed Gold partitions. Final test once after model selection; no direct optimizer feedback from test.
