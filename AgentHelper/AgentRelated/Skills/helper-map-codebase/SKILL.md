---
name: helper-map-codebase
description: Map approved codebase files into AgentHelper project descriptions, create missing descriptions, and verify or correct existing ones before reuse. Use when Codex needs to recommend or save which folders count as the codebase, write or update file descriptions under AgentHelper/ProjectFiles/DescriptionFiles, check whether a description still matches a real file, or correct stale descriptions without documenting dependencies, installed packages, or agent-support files unless the user explicitly asks for them.
---

# Helper Map Codebase

Map approved codebase files into `AgentHelper/ProjectFiles/DescriptionFiles/`, verify existing descriptions against the real files, and keep the approved codebase scope persisted in `AgentHelper/ProjectFiles/CodebaseScope.md`.

## Required Workflow

1. Read `AgentHelper/ProjectFiles/CodebaseScope.md` first when it exists.
2. If no approved scope exists, inspect the repository and recommend the most likely codebase folders to the user.
3. Tell the user they can approve the recommendation with a short confirmation such as `yes` or `do as you know`, or they can provide their own folders.
4. Save the approved scope to `AgentHelper/ProjectFiles/CodebaseScope.md` before mapping files.
5. Discover real files only inside the approved codebase scope unless the user explicitly broadens it.
6. Exclude dependencies, installed packages, generated output, caches, and agent-support folders unless the user explicitly asks for them.
7. Compute the mirrored description path under `AgentHelper/ProjectFiles/DescriptionFiles/`.
8. Check whether a matching description already exists.
9. Read the real file before trusting any existing description.
10. Reuse the existing description only as a draft baseline, not as ground truth.
11. Verify the description against the real file and correct inaccuracies.
12. Create a new description only when no valid description exists.
13. Report which descriptions were created, verified, corrected, or skipped, and note whether the approved scope changed.

Read [references/workflow.md](references/workflow.md) for the detailed execution flow.
Read [references/verification-checklist.md](references/verification-checklist.md) when checking whether a description is accurate.
Read [references/examples.md](references/examples.md) for path-mirroring and decision examples.

## Core Rules

### 1. Mirror the Real Path

Place each description under `AgentHelper/ProjectFiles/DescriptionFiles/`.

For a single approved root:

- mirror the real path relative to that root
- append `.md` to the real filename

Example:

- approved root: `apps/`
- real file: `apps/server-nextjs/src/app/layout.tsx`
- mirrored description file: `AgentHelper/ProjectFiles/DescriptionFiles/server-nextjs/src/app/layout.tsx.md`

For multiple approved roots:

- keep a top-level folder per approved root inside `DescriptionFiles/`
- append `.md` to the real filename

### 2. Treat Existing Descriptions as Inputs, Not Truth

If a description already exists:

- use it as a base
- verify it against the current real file
- keep correct parts
- remove or fix stale claims
- fill in missing responsibilities or behavior

Do not copy an old description forward without verification.

### 3. Correct Instead of Replacing When Possible

If the skill is called for a file that already has a matching mirrored description:

- verify the existing description first
- update it in place if it is incomplete or inaccurate
- create a fresh description only when the existing one is unusable

### 4. Prefer Evidence From Code

When a description conflicts with the real file, trust the real file.

If accuracy is uncertain:

- inspect nearby imports, call sites, tests, or related files
- narrow uncertain claims instead of inventing detail
- state uncertainty explicitly when needed

### 5. Respect the Approved Scope

Do not map the whole repository by default.

Prefer the folders that contain the real application or library code for the current project.

Do not include areas such as these unless the user explicitly asks for them:

- `node_modules/`
- `.venv/`
- build output
- caches
- generated artifacts
- `AgentHelper/`
- `.codex/`
- `.claude/`
- `.planning/`

## Output Standard

A good file description should help a later agent answer:

- what this file is for
- what the main responsibilities are
- what important inputs, outputs, or side effects exist
- what other files or systems it strongly interacts with
- whether the file is stable infrastructure, project-specific logic, UI, tests, config, or generated output

Keep descriptions concrete. Prefer real behavior over abstract wording.

## Execution Notes

- Preserve useful existing phrasing only after it is verified.
- When auditing a folder, handle the most central files first.
- Save descriptions with the real filename plus `.md`.
- Keep `CodebaseScope.md` current when the approved roots change.
