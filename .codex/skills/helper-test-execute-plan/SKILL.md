---
name: helper-test-execute-plan
description: Execute an already prepared automated testing plan one wave at a time when the user explicitly asks to run that plan or a named wave; invoke the local-cover and audit helper skills explicitly; and keep GLOBAL_AUTOTEST_EXECUTION.md resumable with current state, blockers, and the next command.
---

# Helper Test Execute Plan

Execute an existing prepared plan one wave at a time and validate each wave before moving on.
Use this only for execution of a prewritten plan such as `GLOBAL_AUTOTEST_PLAN.md`, not for planning or auditing.

## Required Workflow

1. Read `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`.
2. Read `GLOBAL_AUTOTEST_PLAN.md` and `GLOBAL_AUTOTEST_EXECUTION.md`.
3. Run a preflight check before any wave work:
   - confirm the plan and execution log both exist
   - confirm they contain enough structure to identify the requested wave or the next unfinished wave safely
   - if either artifact is missing or too malformed to continue safely, stop, record an explicit blocker in `GLOBAL_AUTOTEST_EXECUTION.md` when possible, and tell the user what must be fixed first
4. Select the wave:
   - if the user names a specific wave, use it when the artifacts support it
   - otherwise resume a wave already marked `in_progress`
   - otherwise select the earliest wave not marked `complete`
5. Mark the selected wave as `in_progress` in `GLOBAL_AUTOTEST_EXECUTION.md` before editing tests.
6. Break the selected wave into disjoint local scopes such as one route family, one provider, one app segment, or one runtime area.
7. For each scope, explicitly run the `helper-test-local-cover` workflow.
8. After the scoped work for the wave, explicitly run the `helper-test-audit` workflow once for the combined affected wave scope before marking the wave complete.
9. Update `GLOBAL_AUTOTEST_EXECUTION.md` with the minimum wave-tracking fields:
   - wave identifier
   - status: `pending`, `in_progress`, `blocked`, or `complete`
   - completed scopes
   - commands run
   - failures encountered
   - blockers
   - remaining risk
   - current wave
   - next wave
   - next recommended command
10. End each run with a resumable handoff to the user that states:
   - whether the wave is `complete`, `blocked`, or still `in_progress`
   - the current step
   - the next step
   - the exact command to run next, such as continuing the blocked wave or executing the next numbered wave
11. Stop when the wave is complete, blocked, paused by the user, or no safe next action exists.

## Delegation Rules

- Reuse existing agents only when they already exist or the user explicitly asked for delegated or parallel work.
- Only parallelize disjoint write scopes.
- Never let multiple workers edit the same test folder at the same time.
- If the wave depends on missing framework bootstrap, stop the wave and record that dependency explicitly.

## Guardrails

- Do not skip the wave-level validation checkpoint after local test additions.
- Do not mark a wave complete from green local test runs alone when the wave specifically required broader coverage.
- Do not emulate `helper-test-local-cover` or `helper-test-audit` loosely when the task depends on their explicit workflows.
- Keep the execution log resumable for a later fresh context window.
- If the execution log does not already contain a stable wave tracker, add only the minimum structure needed to record the blocker or current state; do not invent wave completion from incomplete artifacts.

## Execution Log Expectations

`GLOBAL_AUTOTEST_EXECUTION.md` should stay readable in a fresh context window. At minimum, keep:

- a wave summary section with current wave, next wave, and overall status
- one per-wave entry or table row with stable statuses: `pending`, `in_progress`, `blocked`, `complete`
- the commands run for the current wave
- blockers and remaining risk
- the next recommended command in exact runnable form, for example `Use $helper-test-execute-plan wave 2`
