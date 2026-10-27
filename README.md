# Financial TABSA - Training Add-on - Stage A

**Cài vào dự án đã tạo từ kit `financial_tabsa_starter_windows.zip`.**

Bước cần có trước: 01 (GPU smoke), 02 (download), 03 (audit), 04 (annotation template). Ít nhất phải có `data/processed/vi_company_dapt_candidates.csv`. Không sử dụng nhãn LLM làm Gold test.

PowerShell:

```powershell
cd D:\financial-tabsa
.\.venv\Scripts\Activate.ps1
# Copy scripts/05_train_stage_A_dapt.py from this add-on to D:\financial-tabsa\scripts\
python scripts\05_train_stage_A_dapt.py --mode prepare
python scripts\05_train_stage_A_dapt.py --mode smoke
```

Xem thêm `docs/STAGE_A_GUIDE_WINDOWS.md`.
