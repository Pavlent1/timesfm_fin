---
name: helper-sync-codex-skills
description: Sync reusable AgentHelper skills from AgentHelper/AgentRelated/Skills into the repo-local .codex/skills runtime directory so they become slash-callable and stay current after edits. Use when a helper-* skill was created, updated, renamed, removed, or is missing from the slash picker, or when Codex needs to refresh the generated mirror after skill changes.
---

# Helper Sync Codex Skills

Refresh the repo-local `.codex/skills/` mirror from the reusable AgentHelper skill source tree.

## Required Workflow

1. Treat `AgentHelper/AgentRelated/Skills/` as the source of truth.
2. Run `scripts/install-agenthelper-skills.ps1` from the repository root.
3. If the user names specific skills, pass them with `-Name`.
4. If no specific skills are named, sync all reusable `helper-*` skills.
5. Verify each requested mirror exists under `.codex/skills/`.
6. Report which mirrors were created, updated, or removed.

## Invocation

- Mention `$helper-sync-codex-skills` to run this workflow.
- Treat any text after the skill name as optional skill names to pass to `-Name`.

## Execution Notes

- Do not edit `.codex/skills/helper-*` copies directly unless the user explicitly wants to bypass the generated mirror flow.
- When a helper skill changes, rerun the installer so the runtime copy matches the source.
- If the slash picker still does not show the skill after syncing, tell the user the runtime may need a session or UI refresh.
