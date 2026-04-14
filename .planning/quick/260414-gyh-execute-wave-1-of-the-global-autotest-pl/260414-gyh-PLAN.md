---
feature: quick-260414-gyh-wave-1-autotest
stage: complete
status: complete
updated: 2026-04-14
context: none
---

# Quick Task 260414-gyh - Execute Wave 1 Of The Global Autotest Plan

## Outcome

Complete Wave 1 of the global autotest roadmap by restoring the required `scripts/testing/` helpers, introducing a stable pytest marker split with an always-runnable `-m "not docker"` subset, and refreshing the saved audit artifacts from the new commands.

## Planning Guardrails

- Keep the repo-managed full-suite pre-commit gate unchanged in this wave.
- Execute the wave in three scopes only:
  - Scope A: tooling bootstrap under `scripts/testing/`
  - Scope B: pytest marker/config split and the non-Docker subset
  - Scope C: audit refresh and execution-log closeout
- Use the existing pytest style for neighboring tests instead of introducing a new Node test runner.

## Inputs Used

- `AGENTS.md`
- `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`
- `AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_PLAN.md`
- `AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_EXECUTION.md`
- `.codex/skills/helper-test-execute-plan/SKILL.md`
- `.codex/skills/helper-test-local-cover/SKILL.md`
- `.codex/skills/helper-test-audit/SKILL.md`
- `.planning/STATE.md`

## Scope Plan

### Scope A: `scripts/testing/` helper restoration

- Add the missing helper suite needed by the test-execution workflow.
- Add small adjacent pytest coverage for the new script outputs using the existing pytest stack.

### Scope B: pytest marker/config split

- Register `unit`, `contract`, `integration`, and `docker` markers.
- Auto-classify the current tests so `pytest -m "not docker"` yields the always-runnable subset.
- Validate the new subset and collect-only behavior.

### Scope C: audit refresh

- Run the restored helper commands and relevant pytest commands.
- Refresh `TEST_BASELINE.md`, `TEST_INVENTORY.md`, and `TEST_AUDIT.md`.
- Update `GLOBAL_AUTOTEST_EXECUTION.md`, quick-task summary artifacts, and `.planning/STATE.md`.
