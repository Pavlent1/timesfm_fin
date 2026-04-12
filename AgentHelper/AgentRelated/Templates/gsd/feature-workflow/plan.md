# Feature Plan Template

Template for `.planning/features/<feature-slug>/PLAN.md`.

```md
---
feature: [feature-slug]
stage: plan
status: ready_for_execute
updated: YYYY-MM-DD
context: ./CONTEXT.md
---

# [Feature Name] - Plan

## Outcome

[What will exist when this feature is complete.]

## Planning Guardrails

- Honor the feature boundary from `CONTEXT.md`
- Do not expand into deferred ideas
- Call out blockers instead of hiding them

## Inputs Used

- `./CONTEXT.md`
- `[path/to/brief-or-prd-if-any]`
- `[relevant project docs if any]`

## Relevant Code

- `[path/to/file]`: [Why it matters]
- `[path/to/file]`: [Why it matters]

## Assumptions

- [Assumption that execution will rely on]

## Blockers

- [Blocking ambiguity or dependency, or `None`]

## Execution Waves

### Wave 1

#### Track: [track-name]
- Objective: [What this track delivers]
- Write Scope: `[path/one]`, `[path/two]`
- Depends on: [None or another track]
- Risks: [Main risk]
- Tasks:
  - [ ] [Concrete task]
  - [ ] [Concrete task]
- Verification:
  - [ ] [Command or check]
  - [ ] [Behavior to confirm]
- Checkpoint: [None | decision | human-verify | human-action]

### Wave 2

#### Track: [track-name]
- Objective: [What this track delivers]
- Write Scope: `[path/one]`
- Depends on: [Track from earlier wave]
- Risks: [Main risk]
- Tasks:
  - [ ] [Concrete task]
- Verification:
  - [ ] [Command or check]
- Checkpoint: [None | decision | human-verify | human-action]

## Verification Strategy

- [Repo-level checks]
- [Feature-specific checks]

## Done Definition

- [Observable completed behavior]
- [Required verification result]
- [Required documentation state]

---

## Handoff

Next command: `$execute [Feature Name]`
Execution should follow these tracks in order, update task progress when useful, and record deviations in `EXECUTION.md`.
```

Guideline: the executor should not need to invent missing structure.
