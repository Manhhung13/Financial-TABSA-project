# Model and agent routing - minimize wasted token usage

## Ground rule
Custom agents under `.codex/agents/` are real Codex subagent roles. By default their model INHERITS the parent, while their reasoning levels differ. This pack does not assume your account has a specific premium model. To activate optional pins, use `tools/set_model_pins.ps1` only after verifying availability in your Codex session.

| Role | Task type | Suggested model class (if available) | Effort | Notes |
|---|---|---|---|---|
| scout | Quick code inventory, file lookup, concise summary | fast (`gpt-6-luna`) | low | Never edit; <=12 lines |
| data_worker | CSV schema, dedup, manifests, simple transformations | fast (`gpt-6-luna`) | medium | Small scoped diffs + tests |
| implementer | Nontrivial Python code, PEFT integration, bug fixes | deep (`gpt-6.1-sol`) | medium | One task at a time |
| ml_architect | Encoder/head transfer, leakage, difficult ML decisions | deep (`gpt-6.1-sol`) | high | Design/review; minimal reads |
| reviewer | Read-only PR review, correctness, reproducibility | deep (`gpt-6.1-sol`) | high | Return concrete findings only |

Names above follow official Codex documentation examples at the time of authoring; entitlements and names can vary. If unsupported, keep model fields unset and let the model inherit the active parent. Never claim arbitrary model-specific billing savings.

## Delegation policy
- Default: one parent agent, zero subagents for small tasks.
- Delegate at most two independent bounded subtasks for complex tasks (e.g. scout code + reviewer of data contract). Parallel write operations over same files are forbidden.
- Parent passes task ID, file scope, acceptance, max output lines. Subagent reads one task and one or two linked docs only.
- Do not spawn an expensive thinker for listing files, formatting Markdown or routine unit test execution.
- Escalate to ml_architect for adapter incompatibility, split leakage or model evaluation design.

## Token-control workflow
`AGENTS.md (~short) -> state/CURRENT.md -> ONE tasks/T-XXX -> referenced docs only -> targeted rg/files -> edit/test -> concise handoff`.
Do not repeatedly paste the proposal, reload entire repository or include huge logs. Keep status and handoff under 12 lines; store detailed evidence in files with path references.

## Optional model pin command (PowerShell)
`powershell -ExecutionPolicy Bypass -File .\tools\set_model_pins.ps1 -FastModel gpt-6-luna -DeepModel gpt-6.1-sol`
It creates backups, updates agent TOML and runs a TOML parse check. Use `-DryRun` first. This is OPT-IN only.

## Official references
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-advanced
- https://learn.chatgpt.com/docs/skills
