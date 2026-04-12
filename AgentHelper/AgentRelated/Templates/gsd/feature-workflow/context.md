# Feature Context Template

Template for `.planning/features/<feature-slug>/CONTEXT.md`.

```md
---
feature: [feature-slug]
stage: discuss
status: ready_for_plan
updated: YYYY-MM-DD
source: [chat | prd:<path> | mixed]
---

# [Feature Name] - Context

## Goal

[One paragraph on what this feature should achieve for the user or operator.]

<boundary>
## Feature Boundary

### In Scope
- [What the feature includes]

### Out of Scope
- [What the feature explicitly does not include]

</boundary>

<success>
## Success Looks Like

- [Observable outcome]
- [Observable outcome]

</success>

<decisions>
## Locked Decisions

### [Area discussed]
- [Concrete decision]
- [Concrete decision]

### Claude's Discretion
- [Areas the planner and executor may choose freely]

</decisions>

<open_questions>
## Open Questions

- [Question that still needs resolution, or `None`]

</open_questions>

<existing_code>
## Existing Code Insights

### Reusable Assets
- `[path/to/file]`: [What is reusable here]

### Integration Points
- `[path/to/file]`: [Where the feature connects]

### Constraints
- [Existing convention or technical constraint]

</existing_code>

<specifics>
## Specific References

- [Examples, references, or "make it like X" guidance]

</specifics>

<deferred>
## Deferred Ideas

- [Out-of-scope idea saved for later]

</deferred>

---

## Handoff

Next command: `$plan [Feature Name]`
Planning should focus on the locked decisions above and treat open questions as explicit planning inputs.
```

Guideline: capture decisions another agent can act on without rereading the full conversation.
