---
feature: quick-260413-wav-test-preferences
stage: plan
status: ready_for_execute
updated: 2026-04-13
context: none
---

# Quick Task 260413-wav - Capture Default Test Automation Preferences Plan

## Outcome

Create an initial `TEST_PREFERENCES.yaml` for the repository, grounded in the current repo state and clearly separated into confirmed policy versus scaffolded defaults.

## Planning Guardrails

- Keep defaults conservative and explicitly unconfirmed.
- Preserve repo reality: only `pytest` is currently detected, and integration tests depend on PostgreSQL via Docker Compose.
- Do not invent CI policy, hard thresholds, or E2E tooling that the repo does not already support.

## Inputs Used

- `AGENTS.md`
- `AgentHelper/AgentRelated/Skills/helper-test-preferences/SKILL.md`
- `AgentHelper/AgentRelated/ARCHITECTURE.md`
- `AgentHelper/ProjectFiles/CodebaseScope.md`
- `.planning/STATE.md`
- `tests/conftest.py`
- `tests/test_discovery_cli.py`

## Relevant Code

- `tests/conftest.py`: Shows that integration tests use `pytest`, Docker Compose, and PostgreSQL fixtures.
- `tests/test_discovery_cli.py`: Confirms current test focus includes discovery and integrity CLI behavior.
- `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`: New durable policy artifact for later QA skills.

## Assumptions

- The user's `use defaults` response means conservative defaults should be saved without upgrading them to confirmed policy.
- A purpose-built YAML schema is clearer here than forcing a document template onto a configuration artifact.

## Blockers

- `scripts/testing/discover-test-landscape.mjs` is missing, so test-landscape detection had to be performed manually.

## Execution Waves

### Wave 1

#### Track: policy-capture
- Objective: Save an actionable first-pass test policy and record the quick task in `.planning`.
- Write Scope: `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`, `.planning/quick/260413-wav-capture-default-test-automation-preferen/260413-wav-SUMMARY.md`, `.planning/STATE.md`
- Depends on: None
- Risks: Overstating defaults as confirmed policy
- Tasks:
  - [ ] Create `TEST_PREFERENCES.yaml` with empty `confirmed_policy` and explicit `scaffolded_defaults`.
  - [ ] Record the quick-task plan and summary artifacts.
  - [ ] Update `.planning/STATE.md` after the artifact commit hash is known.
- Verification:
  - [ ] Confirm the YAML captures only repo-supported runners and constraints.
  - [ ] Confirm defaults are marked unconfirmed.
  - [ ] Confirm quick-task bookkeeping points to the created artifacts.
- Checkpoint: None

## Verification Strategy

- Review the saved YAML for confirmed-versus-unconfirmed separation.
- Verify quick-task artifacts exist under `.planning/quick/260413-wav-capture-default-test-automation-preferen/`.

## Done Definition

- `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` exists and is usable by later helper QA skills.
- The quick task is recorded in `.planning`.
- The saved policy is conservative, factual, and explicitly unconfirmed.

---

## Handoff

Next command: `helper-test-audit` or `helper-test-plan` after policy confirmation or acceptance of the scaffolded defaults.
