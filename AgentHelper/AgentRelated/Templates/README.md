# AgentHelper Template Library

## Purpose

This directory is the reusable template library for `AgentHelper`.

Use it when a task needs to create a durable artifact with a repeatable structure, especially when:

- the artifact will be read by another agent later
- the same document type is likely to appear in multiple repositories
- consistency matters more than inventing a custom one-off format

The goal is to make templates the default path in most cases, not the exception.

## Core Rule

When an agent needs to create a recurring artifact, it should:

1. check this template library first
2. reuse the closest matching template
3. adapt the content to the task
4. only create a new template when no existing template fits reasonably well

Do not start from a blank file if an existing template already covers the artifact shape.

## Current Structure

```text
AgentHelper/AgentRelated/Templates/
|-- README.md
`-- gsd/
    |-- feature-workflow/
    `-- get-shit-done/
```

## Provenance

The templates under `gsd/` were copied from the repository's current GSD libraries:

- `.codex/get-shit-done/templates/`
- `.codex/feature-workflow/templates/`

They are intentionally preserved in a namespaced layout so future updates can be compared, refreshed, or replaced without losing where they came from.

## What To Use Templates For

Use a template whenever you are creating:

- context or discovery docs
- planning artifacts
- execution or summary docs
- verification or UAT docs
- UI contracts
- codebase mapping/reference docs
- project-level planning/state documents

Typical examples:

- feature planning handoff
- execution log
- investigation summary
- validation report
- architecture reference
- test audit
- operator checklist

## When Not To Force A Template

Do not force a template when:

- the output is truly one-off and not reusable
- the template would require more rewriting than writing a small custom file
- the task is only a short note or scratch artifact
- the output is code or configuration rather than a document-style artifact

If you skip a template, do it deliberately and say why.

## Template Selection Workflow

Use this order:

1. `gsd/feature-workflow/`
   Use for named feature artifacts like feature context, plan, and execution logs.
2. `gsd/get-shit-done/`
   Use for phase, project, verification, summary, UI, and broader planning artifacts.
3. `gsd/get-shit-done/codebase/`
   Use for codebase mapping and reference documents.
4. `gsd/get-shit-done/research-project/`
   Use for research packs and project-discovery outputs.

If multiple templates are plausible, choose the one whose downstream use is closest to your task.

## How To Apply A Template

When using a template:

1. copy the template into the target artifact location
2. keep the section structure unless the task clearly does not need part of it
3. replace placeholders with task-specific content
4. remove sections that are truly not applicable rather than leaving filler text
5. preserve headings that downstream agents or humans may rely on

Good use:

- keep the original skeleton
- fill it with concrete repo/task-specific details
- trim irrelevant sections cleanly

Bad use:

- copy a template and leave placeholders behind
- keep irrelevant sections full of empty boilerplate
- invent a new structure while still claiming to use the template

## Imported Template Sets

### `gsd/feature-workflow/`

These are lighter-weight stage artifacts for feature-scoped work:

- `context.md`
- `plan.md`
- `execution.md`

Use them for:

- focused feature discovery
- feature-specific planning
- resumable execution logs

### `gsd/get-shit-done/`

These are broader workflow and planning templates, including:

- `project.md`
- `roadmap.md`
- `requirements.md`
- `state.md`
- `context.md`
- `summary*.md`
- `UAT.md`
- `VALIDATION.md`
- `verification-report.md`
- `UI-SPEC.md`
- `discovery.md`
- `research.md`

Use them for:

- repo-level planning systems
- phase-style orchestration
- verification-heavy workflows
- durable operational artifacts

### `gsd/get-shit-done/codebase/`

These are for codebase reference sets:

- `architecture.md`
- `concerns.md`
- `conventions.md`
- `integrations.md`
- `stack.md`
- `structure.md`
- `testing.md`

Use them when mapping or documenting a codebase for later agent consumption.

### `gsd/get-shit-done/research-project/`

These are project-research bundle templates:

- `ARCHITECTURE.md`
- `FEATURES.md`
- `PITFALLS.md`
- `STACK.md`
- `SUMMARY.md`

Use them when you need a structured research packet instead of a single memo.

## Template Maintenance

When adjusting this library:

- preserve the copied GSD baseline unless you intentionally fork it
- prefer additive documentation over silent rewrites
- if a template becomes AgentHelper-specific, document that divergence clearly
- if a new template is added, place it in a stable category with a clear purpose

If you substantially change imported templates, note whether they are:

- unchanged GSD copy
- lightly adapted copy
- AgentHelper-native template

## Default Expectation

For reusable AgentHelper work, the default assumption should now be:

`template first, custom format second`

If an agent creates recurring artifacts without checking this library, that should be treated as missing a reusable library asset.
