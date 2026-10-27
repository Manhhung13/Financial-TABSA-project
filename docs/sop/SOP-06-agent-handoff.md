# SOP-06: Agent/human handoff
At end of bounded task, write to `state/HANDOFF.md`: task ID, summary (<=2 lines), changed files (paths only), tests (command + PASS/FAIL), assumptions, blockers, next recommended task. Keep <=12 lines and do not paste full stack traces. Store verbose logs in local `artifacts/logs/` or user-provided location.
Only update `state/CURRENT.md` when a task is verified; no speculative DONE.
