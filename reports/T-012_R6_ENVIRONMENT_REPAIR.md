# T-012 R6 — Python Environment Repair & Validation

**Status: BLOCKED at dependency-manifest preflight.** No environment backup/recreation or package installation was started. Per task instructions, stop when the documented required auxiliary manifest conflicts with the reviewed exact pin and requires a policy/pin decision.

## Evidence

- `README_WINDOWS.md:8` instructs users to install `requirements_extra.txt` as the project setup command.
- `requirements_extra.txt` specifies `pandas>=2.0,<3`.
- `requirements.txt` pins `pandas==3.1.0` and also pins the requested ML stack, including `torch==2.6.0+cu124` and `transformers==4.56.1`.
- The two manifests cannot be installed together because their pandas requirements have an empty intersection. The auxiliary file also does not contain Torch, Transformers, PEFT, Datasets or Accelerate, so following the README command alone would not install the requested ML stack.
- R5 confirms `.venv` is broken and that an existing Conda Python 3.11.15 interpreter at `C:\Users\HungT\miniconda3\envs\datathon26\python.exe` is available. No `.venv` operations were run in R6.

## Decision needed before continuing

Choose one manifest policy:

1. **Canonical lock policy:** designate `requirements.txt` as the complete environment lock and treat `requirements_extra.txt` as legacy/unused. Update the setup guidance in a separately authorized documentation change before environment repair; install only `requirements.txt` afterward.
2. **Required auxiliary policy:** retain `requirements_extra.txt` in setup and explicitly approve a pandas constraint change that is compatible with the chosen exact lock. Do not proceed until that pin policy is approved and the manifest is reconciled.

No versions were changed or inferred. The report does not choose between these policies.

## Environment and validation status

- **CPU runtime:** R5 established that Conda base Python 3.13.12 can run CPU smoke checks and compile project scripts, but project `.venv` remains unusable. R6 did not rerun CPU validation because it stopped before environment mutation.
- **CUDA runtime:** R5 observed CUDA availability only in the separate `khdl-gpu` environment (Torch 2.11.0+cu128). The project-pinned Torch 2.6.0+cu124 runtime remains unverified. No CUDA test, GPU forward pass, model download or training was run in R6.
- **Backup:** not created; no destination was reserved because the manifest gate blocked the repair sequence.
- **Restore state:** unchanged. Existing `.venv` was not moved, deleted or overwritten.
- **Governance:** `.codex/config.toml`, `.bak`, `.disabled` and policy files were not changed.
- `pip check`, project dependency imports and project CPU smoke tests were not run. Therefore R6 is not PASS.

After a manifest policy is approved, resume by verifying a timestamped backup destination is absent, moving the existing `.venv` without deleting it, creating a fresh venv with the existing Python 3.11.15 interpreter, installing the exact approved manifest set, then running `pip check`, imports/version checks and CPU smoke tests. Keep CUDA as a separate gate and do not run the download-based GPU smoke script in R6.
