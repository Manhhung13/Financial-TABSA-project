# Scoped agent rules for src/
Before editing code, read root AGENTS.md and active task. Change only task-allowed modules. Python code must use pathlib, UTF-8 and Windows-compatible APIs. Keep raw data immutable; do not hard-code model or dataset secrets. Add focused tests for schema, split, tokenizer/head compatibility. Do not auto-download pretrained checkpoints in unit tests.
