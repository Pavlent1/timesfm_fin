---
name: helper-qa-agent
description: Coordinate repository QA and test-automation work through one entrypoint. Use when Codex needs to choose or run test-policy setup, test-gap analysis, phased test planning, plan execution, local coverage for changed code, or a planner-ready QA handoff based on AgentHelper/ProjectFiles/TestAutomation artifacts.
---

# Helper QA Agent

Use this as the default AgentHelper QA entrypoint when the user asks for testing help without naming the exact helper-test skill.
Route to the narrowest underlying helper workflow, keep the TestAutomation artifacts aligned with the real repo state, and produce a short planner-facing brief when another planning agent needs the QA state in one place.

## Required Workflow

1. Read `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` when it exists.
2. Read the current `TEST_AUDIT.md`, `TEST_BASELINE.md`, `TEST_INVENTORY.md`, `GLOBAL_AUTOTEST_PLAN.md`, and `GLOBAL_AUTOTEST_EXECUTION.md` when they exist, but treat them as leads until refreshed by the appropriate workflow.
3. Decide the operating mode from the request:
   - policy or QA defaults: use `helper-test-preferences`
   - current state, missing tests, invalid tests, or coverage analysis: use `helper-test-audit`
   - phased roadmap, prioritization, or planner-ready sequencing: use `helper-test-plan`
   - execution of an existing test plan or a named wave: use `helper-test-execute-plan`
   - local coverage for changed code only: use `helper-test-local-cover`
4. If prerequisites are missing, route to them first instead of improvising:
   - missing or draft preferences block trustworthy repo-wide planning and plan execution
   - missing or stale audit artifacts block trustworthy repo-wide planning
   - missing plan or execution log blocks plan execution
5. Run only the smallest workflow that satisfies the request. Do not widen local coverage work into a repo-wide audit unless the user asks.
6. When the request involves a planner, roadmap owner, or "what should QA do next", create or refresh `AgentHelper/ProjectFiles/TestAutomation/QA_PLANNER_BRIEF.md` using [references/planner-handoff.md](references/planner-handoff.md).
7. End with the current QA status, the next recommended step, and the exact helper-skill command to continue.

## Mode Selection

### Policy Setup

Use `helper-test-preferences` when the repository lacks confirmed testing policy or when the user wants to change QA rules.

### Analysis

Use `helper-test-audit` when the goal is to understand existing unit, integration, or E2E health, missing coverage, invalid assertions, flaky patterns, or incorrect test-layer choices.

### Planning

Use `helper-test-plan` when the goal is to convert measured QA gaps into waves with priorities, acceptance criteria, and validation commands that another agent can execute safely.

### Execution

Use `helper-test-execute-plan` when `GLOBAL_AUTOTEST_PLAN.md` already exists and the user wants a wave executed, resumed, or unblocked.

### Local Coverage

Use `helper-test-local-cover` when the request is tied to currently changed files and does not justify a repo-wide QA campaign.

## Planner Handoff

When a planner-facing summary is requested:

1. Read the latest audit, baseline, inventory, plan, and execution log that are relevant to the requested scope.
2. State whether the evidence is fresh enough to plan from. If not, recommend the refresh step first.
3. Write or refresh `AgentHelper/ProjectFiles/TestAutomation/QA_PLANNER_BRIEF.md` with:
   - scope and date
   - current QA maturity and largest risks
   - prerequisite artifacts and whether they are fresh
   - recommended next wave or decision
   - dependencies or blockers
   - validation gates and exact follow-up commands
4. Keep the brief short enough for another agent to consume quickly. Do not duplicate whole audits or plans.

## Guardrails

- Do not claim analysis without real repo evidence.
- Do not execute plan work from a missing or malformed plan.
- Do not let planner handoffs drift away from the current QA artifacts.
- Do not replace the specialized `helper-test-*` skills; orchestrate them.
- Do not hand-edit `.codex/skills/helper-*` mirrors.

## Reference

Use [references/planner-handoff.md](references/planner-handoff.md) for the routing matrix and the expected `QA_PLANNER_BRIEF.md` structure.
