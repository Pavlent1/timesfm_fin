---
name: helper-test-plan
description: Create or refresh the repo-wide automated testing roadmap from TEST_AUDIT.md, measured baseline data, saved preferences, and current gaps, then write phased waves with acceptance criteria to GLOBAL_AUTOTEST_PLAN.md.
---

# Helper Test Plan

Create a phased repo-wide testing roadmap, not a flat backlog.
Default to the whole approved codebase unless the user explicitly narrows the scope.

## Required Workflow

1. Read `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`. If it is missing or still draft, stop and direct the user to run `helper-test-preferences` first.
2. Read the current `AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_PLAN.md` when it exists before updating it.
3. Read `TEST_AUDIT.md`, `TEST_BASELINE.md`, and `TEST_INVENTORY.md`.
4. If the audit, baseline, or inventory is missing or obviously stale for the requested scope, refresh them first with the `helper-test-audit` workflow.
5. Run `node scripts/testing/discover-test-landscape.mjs [--scope <scope>] --markdown`. Omit `--scope` when the user did not request a narrower scope.
6. Run `node scripts/testing/summarize-test-gaps.mjs [--scope <scope>] --markdown`. Omit `--scope` when the user did not request a narrower scope.
7. Plan for the whole approved codebase by default unless the user explicitly narrowed the request.
8. Prioritize work using these dimensions:
   - user-facing risk
   - business-critical logic risk
   - failure-path risk
   - measured gap size
   - framework readiness
   - maintenance cost
   - execution speed
   - flake risk
9. Break the work into waves instead of one large unstructured list.
10. For each wave, define:
   - scope
   - why it matters now
   - preferred test layer
   - acceptance criteria
   - validation commands or execution gates
   - dependencies or blockers
11. Write or update `AgentHelper/ProjectFiles/TestAutomation/GLOBAL_AUTOTEST_PLAN.md`.
12. Keep the plan executable by `helper-test-execute-plan`; do not hide key decisions, validation commands, or gating assumptions in prose only.

## Recommended Wave Order

1. audit refresh
2. highest-risk missing regressions
3. contract and integration gaps
4. E2E readiness or bootstrap, only if preferences support it
5. cleanup and hardening

## Guardrails

- Do not assume E2E bootstrap is approved.
- Do not mark a wave ready when its validation gate is vague.
- Prefer measured hotspots over stale audit notes when they conflict.
- Do not proceed without real test preferences; route the user to `helper-test-preferences` first when preferences are missing or still draft.
