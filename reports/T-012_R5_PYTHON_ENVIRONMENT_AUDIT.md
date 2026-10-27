# T-012 R5 — Python Environment Readiness

**R5 runtime gate: WARN for CPU-only audit work; BLOCKED for project ML/CUDA execution.** No environment, dependency, dataset or checkpoint was changed. No installation, upgrade, training, or GPU smoke test was run.

## Diagnosis and interpreter inventory

`.venv/pyvenv.cfg` records Python **3.11.7** at `C:\Users\HungT\AppData\Local\Programs\Python\Python311\python.exe`. Invoking `.venv\Scripts\python.exe` returns “Unable to create process” for that base executable. Direct invocation of the recorded interpreter returns Windows **Access is denied** in this execution context. The Python launcher `py` is not installed/available. Thus the project venv cannot start; the precise underlying OS cause (deleted interpreter files versus access policy) cannot be distinguished here. Do not describe the interpreter as confirmed deleted.

| Interpreter | Observed version | Result |
|---|---:|---|
| `D:\financial-tabsa\.venv\Scripts\python.exe` | intended 3.11.7 | **BLOCKED**; launcher cannot create the recorded base process |
| `C:\Users\HungT\miniconda3\python.exe` | 3.13.12 | Runs; CPU audit runtime with NumPy 2.4.4, pandas 3.0.2, scikit-learn 1.8.0; no Torch/Transformers/PEFT/Datasets/Accelerate |
| `C:\Users\HungT\miniconda3\envs\datathon26\python.exe` | 3.11.15 | Runs; Torch and project ML libraries not installed |
| `C:\Users\HungT\miniconda3\envs\khdl-gpu\python.exe` | 3.12.13 | Runs; Torch 2.11.0+cu128 reports `torch.cuda.is_available() == True`; Transformers, PEFT, Datasets, Accelerate absent |
| standalone Python 3.12 path | unverified | Direct launch denied by the same filesystem/execution boundary; not used |

## Dependency and compatibility evidence

`requirements.txt` pins Torch 2.6.0+cu124, Transformers 4.56.1, PEFT 0.17.1, Datasets 3.6.0, Accelerate 1.10.1, NumPy 2.4.6 and pandas 3.1.0, among other exact versions. The corresponding `.venv\Lib\site-packages\*.dist-info` metadata is present for all nine queried packages. Torch, NumPy and pandas wheel tags are `cp311-cp311-win_amd64`, consistent with Python 3.11 on Windows. Their `Requires-Python` entries permit 3.11. Static dependency metadata is coherent for the core stack: Transformers requires `huggingface-hub>=0.34,<1` (pin 0.36.2); PEFT requires Torch >=1.13 (pin 2.6.0) and Transformers; Accelerate requires Torch >=2 (pin 2.6.0); Datasets requires PyArrow >=15 (pin 26.0.0). This is static metadata evidence only; `pip check` and imports in `.venv` could not run.

**Manifest conflict:** `requirements_extra.txt` allows pandas `>=2,<3`, while `requirements.txt` pins pandas `==3.1.0`. Installing both files together is unsatisfiable. Decide whether the extra manifest is obsolete/optional or revise the constraints under a separately authorized dependency-maintenance task; no pin was changed here.

The existing GPU smoke script imports Torch/Transformers, checks CUDA and then downloads `FacebookAI/xlm-roberta-base` weights. It was inspected but **not executed**, because it downloads a checkpoint and runs a GPU forward pass. In the separate `khdl-gpu` environment, CUDA availability was observed with Torch 2.11.0+cu128; this does not prove the project's Torch 2.6.0+cu124 environment or its CUDA/cuDNN runtime works. Installed system CUDA toolkit 13.1 alone does not establish the PyTorch wheel's runtime compatibility.

## CPU checks executed

- On existing Conda base Python 3.13.12, imported NumPy 2.4.4, pandas 3.0.2 and scikit-learn 1.8.0; a small in-memory pandas mean operation returned 2.0; standard-library CSV/JSON/SHA-256 smoke passed.
- `python -m compileall -q tools scripts src reports/T-002_DATA_AUDIT.py reports/T-002_TARGET_ALIAS_AUDIT.py` completed successfully using Python 3.13.12. This syntax check does not verify imports against the project's pinned ML stack or invoke audit scripts.
- No project venv import, `pip check`, pytest, GPU forward pass, or model download was attempted.

## Reproducible repair plan (not executed)

1. Preserve the current `.venv` as a dated backup; do not delete it. First verify the intended backup destination does not already exist.
2. After explicit authorization to recreate the environment, use the existing Python 3.11.15 Conda interpreter to create a fresh project venv, e.g. `C:\Users\HungT\miniconda3\envs\datathon26\python.exe -m venv .venv`. This keeps the interpreter family aligned with the CPython 3.11 Windows wheel metadata.
3. Resolve the `requirements_extra.txt` pandas conflict before deciding whether that file belongs in the environment. After separate authorization for package installation, install only the reviewed exact pins from the selected manifest; do not silently upgrade or relax versions.
4. Validate `.venv\Scripts\python.exe -m pip check`, import the pinned packages, rerun the CPU compile/audit checks, and record exact versions. Keep the GPU smoke test as a separate, explicitly authorized operation because it downloads model weights and allocates GPU memory.

## Governance configuration (separate)

`.codex/config.toml` is absent; `.codex/config.toml.bak` and `.codex/config.toml.disabled` exist. The governance validator previously required `.codex/config.toml`. No config was restored or modified: the task explicitly requires leaving the previously incompatible configuration disabled. Treat the governance-config blocker separately from Python runtime readiness.

## Gate decision

- **PASS:** existing Python 3.13.12 supports bounded CPU smoke checks; project source audit scripts compile under it; installed project metadata pins align to CPython 3.11 Windows wheel tags.
- **WARN:** no live `pip check` or ML package import in `.venv`; another CUDA-enabled Torch exists only in `khdl-gpu`, not the target environment.
- **BLOCKED:** project venv cannot launch; exact root OS cause remains unverified; `requirements_extra.txt` conflicts with pandas pin; project Torch/CUDA runtime is untested. R5 is not PASS for automated ML runtime or T-003B processing.
