# SOP-03: Train/transfer runbook
1. Confirm stage-specific task/data contract/head and previous checkpoint manifest.
2. Snapshot config, data hashes, code commit, seeds, base model/tokenizer revision, adapter targets.
3. Run CPU schema tests; GPU forward/backward smoke (batch=1, 128 tokens), record VRAM before larger run.
4. Run training with stage-specific metrics; save checkpoints outside Git and safe on OOM.
5. Check no Gold val/test overlap. Record validation metrics; no test or market claims at this stage.
6. Transition to next stage only after loading previously saved adapter and verifying expected trainable tensors, head compatibility and actual change from fresh initialization.
7. Update state with checkpoint location and manifest, or rollback/blocker; no silent full retraining.
