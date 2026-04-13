---
feature: quick-260413-wfu-precommit-hook
stage: plan
status: ready_for_execute
updated: 2026-04-13
context: none
---

# Quick Task 260413-wfu - Add Pre-Commit Hook To Run All Tests Before Commit Plan

## Outcome

Add a repo-managed pre-commit hook that runs the full pytest suite before each commit and record that policy in the saved test preferences.

## Planning Guardrails

- Keep the hook repo-managed rather than writing one-off local logic into `.git/hooks`.
- Prefer the repository `.venv` because the global Python in this checkout does not have `pytest`.
- Preserve the current test reality: the hook runs the full suite, including Docker Compose backed PostgreSQL integration tests.

## Inputs Used

- `AGENTS.md`
- `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`
- `tests/conftest.py`
- `README.md`

## Relevant Code

- `tests/conftest.py`: Shows that the suite starts PostgreSQL integration dependencies automatically.
- `scripts/precommit-checks.mjs`: New mechanical test gate for the hook.
- `.githooks/pre-commit`: New repo-managed Git hook entrypoint.

## Assumptions

- `node` is available in environments where the repo-managed hook will run.
- The user wants the full suite on every commit, even when integration tests require Docker and may take longer.

## Blockers

- None.

## Execution Waves

### Wave 1

#### Track: hook-implementation
- Objective: Add the mechanical test runner, install the hook path locally, and update policy artifacts.
- Write Scope: `scripts/precommit-checks.mjs`, `.githooks/pre-commit`, `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`, `AgentHelper/ProjectFiles/DescriptionFiles/scripts/precommit-checks.mjs.md`, `.planning/quick/260413-wfu-add-pre-commit-hook-to-run-all-tests-bef/260413-wfu-SUMMARY.md`, `.planning/STATE.md`
- Depends on: None
- Risks: The full suite may block commits when Docker or PostgreSQL is unavailable.
- Tasks:
  - [ ] Create the repo-managed pre-commit runner and hook entrypoint.
  - [ ] Update saved test policy to confirm the pre-commit execution behavior.
  - [ ] Record the quick-task artifacts and local hook installation.
- Verification:
  - [ ] Run the mechanical pre-commit script directly.
  - [ ] Confirm `core.hooksPath` points to `.githooks`.
  - [ ] Confirm the saved policy records pre-commit as confirmed.
- Checkpoint: None

## Verification Strategy

- Execute `node scripts/precommit-checks.mjs`.
- Read back the local `core.hooksPath` setting.

## Done Definition

- `git commit` in this repo uses `.githooks/pre-commit`.
- The hook runs the full pytest suite from the repository root.
- The saved test policy no longer leaves pre-commit behavior unspecified.

---

## Handoff

Next command: `git commit` will trigger the new hook automatically in this local checkout.
