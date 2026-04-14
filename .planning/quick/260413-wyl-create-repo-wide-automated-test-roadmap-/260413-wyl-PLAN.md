---
feature: quick-260413-wyl-global-autotest-plan
stage: plan
status: ready_for_execute
updated: 2026-04-13
context: none
---

# Quick Task 260413-wyl - Create Repo-Wide Automated Test Roadmap From Current Audit Artifacts Plan

## Outcome

Create `AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_PLAN.md` as an execution-ready, wave-based roadmap grounded in the current test preferences, audit, baseline, inventory, and the verified missing-script state.

## Planning Guardrails

- Keep the plan scoped to the whole approved codebase: `src/`, `configs/`, and `scripts/`.
- Do not invent a browser or Playwright E2E wave; the saved preferences explicitly show no approved E2E runner.
- Treat missing `scripts/testing/` helpers and the Docker-gated integration fixture as first-class planning inputs, not cleanup footnotes.

## Inputs Used

- `AGENTS.md`
- `AgentHelper/AgentRelated/ARCHITECTURE.md`
- `AgentHelper/AgentRelated/AdditionalRules/Governance/TemplateFirstArtifacts/RULE.md`
- `AgentHelper/AgentRelated/Templates/README.md`
- `.codex/skills/helper-test-plan/SKILL.md`
- `.codex/skills/helper-test-execute-plan/SKILL.md`
- `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`
- `AgentHelper/ProjectFiles/TestAutomation/TEST_AUDIT.md`
- `AgentHelper/ProjectFiles/TestAutomation/TEST_BASELINE.md`
- `AgentHelper/ProjectFiles/TestAutomation/TEST_INVENTORY.md`
- `.planning/STATE.md`

## Relevant Code

- `tests/conftest.py`: Current shared Docker-backed PostgreSQL fixture that blocks most collected tests when Docker is unavailable.
- `scripts/precommit-checks.mjs`: Current repo-managed full-suite gate that requires Docker before running pytest.
- `src/binance_market_data.py`: Shared Binance pagination, retry, and de-duplication logic called out by the audit as untested.
- `src/bootstrap_postgres.py`: Bootstrap CLI with argument parsing and wait behavior called out by the audit as untested.
- `AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_PLAN.md`: New durable roadmap artifact for downstream execution.

## Assumptions

- The current audit, baseline, and inventory still describe the whole approved scope accurately enough to plan from, even though they contain stale wording about `TEST_PREFERENCES.yaml` still being `draft`.
- Re-running `node scripts/testing/discover-test-landscape.mjs --markdown` and `node scripts/testing/summarize-test-gaps.mjs --markdown` on 2026-04-13 still fails with `MODULE_NOT_FOUND`, so tooling restoration belongs in Wave 1.
- A custom wave-based plan document is clearer for this artifact than forcing a generic feature-plan template verbatim.

## Blockers

- `scripts/testing/discover-test-landscape.mjs`, `scripts/testing/measure-coverage.mjs`, and `scripts/testing/summarize-test-gaps.mjs` are still missing, so the helper workflow cannot refresh measurement automatically before planning.

## Execution Waves

### Wave 1

#### Track: roadmap-authorship
- Objective: Write the global automated test roadmap and record this quick-task handoff cleanly in `.planning`.
- Write Scope: `AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_PLAN.md`, `.planning/quick/260413-wyl-create-repo-wide-automated-test-roadmap-/260413-wyl-SUMMARY.md`, `.planning/STATE.md`
- Depends on: None
- Risks: Producing a narrative memo instead of an execution-ready wave plan
- Tasks:
  - [ ] Convert the verified audit findings into ordered execution waves.
  - [ ] Lock the key planning decisions needed for downstream execution.
  - [ ] Record the quick-task artifacts and state update.
- Verification:
  - [ ] Confirm each wave has scope, why-now rationale, preferred layer, acceptance criteria, validation commands, and dependencies or blockers.
  - [ ] Confirm the plan does not add an unapproved E2E wave.
  - [ ] Confirm the plan keeps the missing helper scripts and Docker dependency visible in Wave 1 and Wave 3.
- Checkpoint: None

## Verification Strategy

- Read the final roadmap end-to-end and verify that each wave is selectable and executable without inventing missing structure.
- Confirm the plan is anchored to the actual saved preferences, not the stale `draft` wording inside the audit artifacts.

## Done Definition

- `AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_PLAN.md` exists and is usable by `helper-test-execute-plan`.
- The roadmap reflects the current whole-repo test posture, with missing tooling and Docker coupling explicitly prioritized.
- The quick task is recorded under `.planning/quick/260413-wyl-create-repo-wide-automated-test-roadmap-/`.

---

## Handoff

Next command: `helper-test-execute-plan` after the user decides which wave to start with.
