# Planner Handoff

Use this reference when `helper-qa-agent` needs to route a request or produce a planner-facing QA brief.

## Routing Matrix

- User asks for QA policy, defaults, or testing rules: run `helper-test-preferences`
- User asks what tests exist, what is broken, or what coverage is missing: run `helper-test-audit`
- User asks for a phased QA roadmap, prioritization, or a plan another agent can execute: run `helper-test-plan`
- User asks to execute or resume a named wave from an existing QA plan: run `helper-test-execute-plan`
- User asks to cover recently changed code only: run `helper-test-local-cover`

## QA Planner Brief Structure

Write `AgentHelper/ProjectFiles/TestAutomation/QA_PLANNER_BRIEF.md` with this shape:

```md
# QA Planner Brief

- Date: YYYY-MM-DD
- Scope: <repo-wide or narrowed scope>
- Evidence freshness: fresh | stale | partial

## Current QA State

- Current maturity summary
- Highest-risk gaps
- Known blockers

## Source Artifacts

- `TEST_PREFERENCES.yaml`: <status>
- `TEST_AUDIT.md`: <status>
- `TEST_BASELINE.md`: <status>
- `TEST_INVENTORY.md`: <status>
- `GLOBAL_AUTOTEST_PLAN.md`: <status>
- `GLOBAL_AUTOTEST_EXECUTION.md`: <status>

## Recommended Next Step

- Preferred helper skill
- Why this is the next step
- Exact command to run

## Validation Gates

- Commands or checks that must pass before the next phase is complete

## Planner Notes

- Sequencing constraints
- Dependencies
- Assumptions that still need confirmation
```

## Brief Quality Bar

- Keep the brief short and current.
- Prefer exact commands over vague recommendations.
- Name stale artifacts explicitly instead of silently planning from them.
- Point the planner at the next wave or refresh step, not at a generic backlog.
