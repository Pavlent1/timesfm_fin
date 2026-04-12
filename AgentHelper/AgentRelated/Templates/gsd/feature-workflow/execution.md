# Feature Execution Template

Template for `.planning/features/<feature-slug>/EXECUTION.md`.

```md
---
feature: [feature-slug]
stage: execute
status: in_progress
updated: YYYY-MM-DD
context: ./CONTEXT.md
plan: ./PLAN.md
---

# [Feature Name] - Execution

## Summary

[Short current status or final outcome.]

## Progress by Track

### [track-name]
- Status: [pending | in_progress | blocked | complete]
- Completed:
  - [Completed item]
- Remaining:
  - [Remaining item or `None`]

## Verification Evidence

- `[command]`: [result]
- [Manual check]: [result]

## Files Changed

- `[path/to/file]`: [Why it changed]

## Deviations from Plan

- [Deviation and rationale, or `None`]

## Issues and Blockers

- [Issue, mitigation, or `None`]

## Next Step

- [Exact next action or `Complete`]

---

## Handoff

[If blocked: `Return to $plan [Feature Name] to resolve blocker.`]
[If complete: `Feature complete.`]
```

Guideline: another agent should be able to resume execution from this file alone.
