# Local Test Gate

## Purpose

This rule makes local test-impact validation part of normal code-change readiness.

## When To Load

Load this rule when a task changes production code, materially changes behavior, or changes tests in a way that could affect behavior.

## Required Behavior

- Run a local test-impact pass before treating the work as ready to commit.
- If the changed area already has tests, audit that affected scope with `helper-test-audit` and strengthen it as needed with `helper-test-local-cover`.
- If the changed area lacks adequate coverage, use `helper-test-local-cover` to add the smallest correct tests for the change.
- Prefer existing local test conventions before introducing a new layer or framework.
- Keep `scripts/precommit-checks.mjs` as the mechanical non-E2E gate.
- Use this rule as the decision gate that answers:
  - whether the change needs new or stronger tests
  - which local validation commands should run beyond the default precommit script
  - whether any explicit blocker must be recorded before commit readiness
- Do not treat code work as commit-ready until the local test-impact pass has either passed or recorded an explicit blocker.
