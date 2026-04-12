# Project File Descriptions

## Purpose

This rule defines how project-file descriptions are created, updated, and reused inside `AgentHelper/ProjectFiles/`.

## When To Load

Load this rule when the task:

- touches, reviews, or edits a project file inside the approved codebase scope
- creates or updates project-file descriptions
- reuses existing descriptions as context for code work
- maps a repository area into the description tree

## Required Behavior

- Read `AgentHelper/ProjectFiles/CodebaseScope.md` first when it exists.
- Treat the saved scope as the default source of truth for which folders count as the codebase.
- When a task touches a project file inside the approved scope, look for the matching description before editing when one exists.
- If no approved scope exists, inspect the repository, recommend the most likely codebase folders, and ask the user to either approve that recommendation or provide different folders.
- Tell the user they can approve the recommendation with a short confirmation such as `yes` or `do as you know`.
- Save the approved scope to `AgentHelper/ProjectFiles/CodebaseScope.md` before mapping or updating descriptions.
- Limit descriptions to approved codebase folders unless the user explicitly asks for broader coverage.
- Exclude dependencies, installed packages, caches, generated output, and agent-support folders unless the user explicitly includes them.
- Store descriptions under `AgentHelper/ProjectFiles/DescriptionFiles/`.
- For a single approved root, mirror the file path relative to that root and append `.md` to the real filename.
- For multiple approved roots, preserve a top-level folder per approved root inside `DescriptionFiles/` and append `.md` to the real filename.
- Verify an existing description against the real file before reusing it.
- Update descriptions in place when they are salvageable; rewrite only when the old description is no longer trustworthy.
- If a touched project file inside the approved scope is created, moved, renamed, or materially changed, create or update its matching description before finishing the task.

## Examples

Single approved root:

- approved root: `apps/`
- real file: `apps/server-nextjs/src/app/layout.tsx`
- description file: `AgentHelper/ProjectFiles/DescriptionFiles/server-nextjs/src/app/layout.tsx.md`

Multiple approved roots:

- approved roots: `apps/`, `scripts/`
- real file: `scripts/install-agenthelper-skills.ps1`
- description file: `AgentHelper/ProjectFiles/DescriptionFiles/scripts/install-agenthelper-skills.ps1.md`
