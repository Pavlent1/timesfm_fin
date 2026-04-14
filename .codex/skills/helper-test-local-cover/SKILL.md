---
name: helper-test-local-cover
description: Add or improve the smallest correct tests for changed code by reading saved test preferences, discovering affected tests, choosing the right level, validating the new tests, and reporting remaining local risk without turning the task into a repo-wide plan.
---

# Helper Test Local Cover

Cover newly created or changed code with the smallest correct local tests.

## Required Workflow

1. Read `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` first.
2. Discover the local scope:
   - if the user names files or folders, use that scope
   - otherwise run `node scripts/testing/find-affected-tests.mjs --markdown` to inspect the current git diff or untracked files
3. Inspect neighboring production files and neighboring tests before deciding what to add.
4. Use `node scripts/testing/classify-test-level.mjs --source <path>` as a heuristic aid, then confirm the final choice from the real code risk:
   - unit for isolated deterministic logic
   - integration when the risk is in wiring, routes, providers, storage, auth, or cross-module behavior
   - E2E only when the user-critical value is proving a whole flow and the repo is configured for it
5. Prefer the local test style already used by neighboring files.
6. If preferences mention Playwright but the repo is not bootstrapped for it, log the dependency instead of silently scaffolding a large E2E system.
7. Create or update the local tests.
8. Rerun the narrowest relevant validation command.
9. Run a validator-style quality pass on the new or changed tests:
   - do they assert real outcomes
   - are they over-mocked
   - do they duplicate an existing scenario
   - do they belong in a different layer
10. Report what changed, what commands passed, and what risk remains.

## Output Standard

- local test changes near the affected code
- targeted validation output in the response
- optional note in `TEST_BASELINE.md` only when a new runner or convention is introduced

## Guardrails

- Do not widen a local coverage request into a global testing roadmap.
- Do not run multiple overlapping editors against the same test folder at once.
- Do not treat code as commit-ready until the local test-impact pass has either passed or recorded an explicit blocker.
