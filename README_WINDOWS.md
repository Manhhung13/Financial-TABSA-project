# Financial TABSA - Windows starter kit (Steps 1-4)

All commands are for **PowerShell**, from an activated virtual environment.

```powershell
cd D:\financial-tabsa
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements_extra.txt
```

## Step 1 - GPU smoke test

```powershell
python scripts\01_gpu_smoke_test.py
```

First run downloads `FacebookAI/xlm-roberta-base`. Cache is stored in `.hf_cache` on your **D:** drive. This step only runs a BF16 inference pass to verify GPU/VRAM. It is not sentiment training.

## Step 2 - Download datasets

```powershell
python scripts\02_download_datasets.py
```

Downloads:
- HF Vietnamese company-tagged corpus (10,400 rows, `Content` + unverified `Label`).
- GitHub English SEntFiN (`SEntFiN.csv` with `Title` and `Decisions`).
- GitHub Thai finance corpus (`56-1dataset_50.csv` with firm/year/section/paragraph/aspect/sentiment).

If you also want the separate general Vietnamese sentiment corpus (3,692 rows):

```powershell
python scripts\02_download_datasets.py --include-vi-sentiment
```

Outputs: `data/raw/..` and `data/raw/download_manifest.json` with checksums.

## Step 3 - Audit and normalize each source separately

If you have your existing LLM-labeled CSV, copy it before audit:

```powershell
Copy-Item 'D:\YOUR_PATH\phobert_dataset.csv' 'D:\financial-tabsa\data\silver\phobert_dataset.csv'
python scripts\03_audit_prepare.py
```

Replace `D:\YOUR_PATH` with the true file location. If the file is missing, the script skips Silver and Step 4 can use Vietnamese company-tagged data instead.

Review `data/processed/audit_summary.json` and `data/processed/vi_company_suspicious_tags.csv`.

DO NOT concatenate all CSVs into one fake joint sentiment/aspect dataset.

## Step 4 - Create a blank human review template

```powershell
python scripts\04_create_gold_review.py --n 100
```

Outputs:
- `data/gold/article_pool_to_verify.csv`: selected source texts and candidate tickers.
- `data/gold/gold_annotation_template.csv`: 5 blank aspect rows per article-target unit.

Open those in Excel. Label `aspect_present` first, then sentiment if present; verify the original target and evidence. `annotation_status` remains `pending` until a human has checked the content. This is NOT yet a Gold train/test dataset.

## If errors occur
- `ModuleNotFoundError`: confirm `.venv` is activated and pip packages were installed there.
- `CUDA out of memory`: close Docker/browser and background GPU processes. Smoke test loads an encoder for inference only.
- `SSL/HTTP` or GitHub/HF errors: retry the download; review `download_manifest.json`.
- `UnicodeDecodeError`: inspect the original CSV encoding before changing code; do not discard accented Thai/Vietnamese text.
- `PermissionError` or disk full: ensure sufficient free disk on D:, and close Excel before overwriting output CSVs.

## Modeling roadmap after this kit
1. Adjudicate human labels and group-deduplicate before splitting.
2. Keep a held-out VI Gold test and exclude near-duplicate content from **all** training/corpus sources.
3. Train XLM-R + LoRA baseline on Gold train.
4. Test VI DAPT, SEntFiN intermediate entity sentiment and Thai ABSA as separate ablations.
5. Do not use Silver score=0 as guaranteed `neutral`/`absent`.

---

## BUOC TIEP: TRAIN STAGE A (after 01..04)

Script bo sung: `scripts/05_train_stage_A_dapt.py`.

```powershell
python scripts\05_train_stage_A_dapt.py --mode prepare
python scripts\05_train_stage_A_dapt.py --mode smoke
```

`prepare` khong train. `smoke` train 5 steps tren RTX 4050 de test thuc te VRAM.
Sau khi khoa Gold heldout va kiem tra trung event, moi chay `--mode train --max-steps 400`.
Huong dan chi tiet: `docs/STAGE_A_GUIDE_WINDOWS.md`.
Phan tiep theo: `docs/STAGES_BCD_PLAN.md`.
