# Verified local context and setup gates

User environment observed in screenshots: Windows PowerShell, Python native on Windows (no WSL), `D:\financial-tabsa`, NVIDIA RTX 4050 Laptop GPU with 6GB dedicated VRAM, 16GB RAM; PyTorch 2.6.0+cu124, CUDA available, BF16 true; Transformers 4.56.1, PEFT 0.17.1, Datasets 3.6.0, Accelerate 1.10.1.

These are observations from conversation screenshots, NOT results of running this kit. Recheck inside `.venv` before changing dependencies or launching GPU jobs.

Read-only sanity commands (PowerShell):
```powershell
cd D:\financial-tabsa
.\.venv\Scripts\Activate.ps1
python --version
python -c "import torch; print(torch.__version__, torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
python -c "import transformers, peft, datasets; print(transformers.__version__, peft.__version__, datasets.__version__)"
```

Windows-safe defaults: `num_workers=0`, paths via pathlib, UTF-8 CSV/JSONL, limit RAM-heavy pandas copies, no WSL-only commands. No forced package updates or model downloads. Check available disk space and RAM before full DAPT.

Existing starter scripts may be `scripts/01_gpu_smoke_test.py`..`05_train_stage_A_dapt.py` from earlier chat. T-001 must confirm actual presence and compatibility before using them.
