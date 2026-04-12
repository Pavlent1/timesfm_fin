---
name: helper-test-audit
description: Audit the repository's existing automated tests across unit, integration, and E2E layers using real discovery, real test commands, and real repo evidence; record invalid, broken, fragile, or misleading tests plus missing-test areas; and write or refresh TEST_AUDIT.md with dated findings that can drive helper-test-plan.
---

# Helper Test Audit

Audit current automated tests from real command output and repo inspection. Treat old audits as leads, not as ground truth.
Default to the whole approved codebase unless the user explicitly narrows the scope.

## Required Workflow

1. Read `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` when it exists. If it is missing or still draft, continue with conservative defaults and say so.
2. Read the current `TEST_AUDIT.md`, `TEST_BASELINE.md`, and `TEST_INVENTORY.md`, but verify them against the repo before trusting them.
3. Run `node scripts/testing/discover-test-landscape.mjs [--scope <scope>] --markdown` to map current runners, configs, and test files. Omit `--scope` when the user did not request a narrower scope.
4. Use the discovery output to explicitly account for unit, integration, and E2E coverage in the requested scope. If one layer is absent, record whether that absence is intentional, unsupported, or a gap.
5. Run the narrowest relevant repo-owned test commands for every discovered runner in scope. If the user did not narrow the scope, audit the whole approved codebase.
6. Run `node scripts/testing/measure-coverage.mjs [--scope <scope>] --markdown` when coverage is available for that scope. If no supported coverage path exists, record coverage as unavailable instead of failing the audit for that reason alone.
7. Run `node scripts/testing/summarize-test-gaps.mjs [--scope <scope>] --markdown` to surface skipped tests, fragile patterns, coverage hotspots, and obvious no-test areas.
8. Inspect the highest-risk suites manually before making quality claims. Treat failed commands, skipped-heavy suites, fragile patterns, over-mocked suites, stale assertions, and suites covering critical app paths as highest-risk by default.
9. Compare the production code layout against the discovered tests so the audit names the obvious no-test or under-tested areas, including missing unit, integration, and E2E coverage where applicable.
10. For each significant suite or missing area, classify the finding clearly:
   - broken or non-functional test execution
   - invalid or misleading assertions
   - fragile or flaky patterns
   - incorrect layer choice
   - missing tests for important behavior
   - missing coverage measurement or missing runnable command
11. Do not widen this audit into implementation work. Do not fix tests or production code unless the user explicitly asks for follow-up execution.
12. Create or update `AgentHelper/ProjectFiles/TestAutomation/TEST_BASELINE.md` with:
   - date
   - commands run
   - pass/fail status
   - coverage numbers when available
   - installed runners detected
   - blockers or unavailable coverage areas
13. Create or update `AgentHelper/ProjectFiles/TestAutomation/TEST_INVENTORY.md` with the current per-app and per-layer map.
14. Create or update `AgentHelper/ProjectFiles/TestAutomation/TEST_AUDIT.md` with:
   - date and scope
   - commands run
   - suite health by app and test layer
   - concrete validity and functionality findings for existing tests
   - concrete missing-test findings for uncovered or under-tested areas
   - blockers, assumptions, and unavailable tooling
   - prioritized next-step recommendations
15. End with a brief user-facing report ordered by severity. If the audit surfaces many issues or broad structural gaps, offer the exact follow-up command for planning, for example `Use $helper-test-plan to turn AgentHelper/ProjectFiles/TestAutomation/TEST_AUDIT.md into a phased improvement plan`.

## Non-Goals

- Do not turn this into a repo-wide implementation campaign.
- Do not introduce a new framework unless the user explicitly asks for bootstrap work.
- Do not silently trust prior audits over current code and command output.
- Do not edit tests or production code unless the user explicitly asks for it.

## Output Standard

- primary artifacts: `TEST_AUDIT.md`, `TEST_BASELINE.md`, `TEST_INVENTORY.md`
- response standard: brief problem summary first, then the audit artifact path, then an exact `helper-test-plan` command when the issue volume warrants planning
