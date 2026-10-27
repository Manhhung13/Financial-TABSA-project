# SOP-01: One-task execution cycle
1. Read `AGENTS.md` (auto), `state/CURRENT.md`, one `tasks/T-XXX...md` and only links in its Context field.
2. Check git status and inspect affected paths/symbols. If absent/ambiguous, record blocker rather than inventing an API.
3. Confirm preconditions, owning agent, allowed files, acceptance criteria and test command.
4. Make a small patch. Run relevant cheap tests first; expensive tests require approval.
5. Produce concise changed-files list, checks, blockers, one next task. Update `state/CURRENT.md` and `state/HANDOFF.md` <=12 lines each.
6. Do not auto-close task based only on code existence. Mark DONE only after acceptance evidence.
Stop if destructive changes, Gold test contamination or unclear label semantics.
