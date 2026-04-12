# Template-First Artifacts

## Purpose

This rule makes reusable templates the default starting point for durable artifacts created under AgentHelper-guided workflows.

## When To Load

Load this rule when the task creates, revises, or standardizes document-style artifacts such as:

- context files
- planning documents
- execution logs
- verification or audit reports
- codebase reference docs
- repeatable research bundles

## Required Behavior

- check `AgentHelper/AgentRelated/Templates/` before inventing a new artifact structure
- prefer the closest existing template when creating recurring artifacts
- preserve the template's structural intent unless the task clearly needs less
- remove irrelevant sections cleanly instead of leaving placeholder noise behind
- if no template fits, create the artifact deliberately and consider whether the library needs a new reusable template

## Default Selection Order

1. `Templates/gsd/feature-workflow/`
2. `Templates/gsd/get-shit-done/`
3. `Templates/gsd/get-shit-done/codebase/`
4. `Templates/gsd/get-shit-done/research-project/`

## Do Not

- do not start recurring artifacts from a blank file without checking the template library first
- do not claim to use a template while leaving unresolved placeholders behind
- do not flatten imported template provenance without a clear reason
- do not copy a template wholesale when a smaller adapted version would be clearer for the task

## Expected Outcome

Most durable AgentHelper artifacts should now be template-derived, even when lightly adapted.
