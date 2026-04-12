# Verification Checklist

Use this checklist when deciding whether an existing description is still accurate.

## Scope Check

- Is the real file inside the approved codebase scope from `AgentHelper/ProjectFiles/CodebaseScope.md`?
- Is the description stored in the correct location under `AgentHelper/ProjectFiles/DescriptionFiles/`?
- Should this file be excluded because it is a dependency, generated artifact, or agent-support file?

## Purpose Check

- Does the description still describe the file's actual role?
- Has the file changed from infrastructure to business logic, UI, test, config, or another category?

## Responsibility Check

- Do the listed responsibilities still exist?
- Are any major responsibilities missing?
- Does the description mention behavior that was removed?

## Interface Check

- Do the exported names or entrypoints still match?
- Does the file now accept different inputs or produce different outputs?

## Dependency Check

- Are the major imports, integrations, or dependent files still the same?
- Did the file gain or lose an important external dependency?

## Side-Effect Check

- Does the file now persist data, call APIs, register routes, or change runtime state differently than described?
- Did previous side effects disappear?

## Scope Check

- Is the description too broad for what the file actually does now?
- Is it too narrow and missing new behavior?

## Language Check

- Is the description specific and evidence-based?
- Does it avoid assumptions that are not visible in the file or nearby code?

## Rewrite Threshold

Prefer a full rewrite in the same mirrored location when:

- most of the existing description is stale
- the file was substantially repurposed
- the previous description is too vague to salvage
