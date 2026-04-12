# AgentHelper AGENTS Template

This file is kept as a reusable template/reference copy.

It is intentionally not named `AGENTS.md`, so runtime agents should not auto-load it by filename alone.

When working on `AgentHelper/` from this repository, start from the repo-root `AGENTS.md`, which routes into this template where relevant.

## Purpose

This file is the library-level instruction template for `AgentHelper`.

`AgentHelper` separates reusable agent assets from project-specific artifacts:

```text
AgentHelper/
|-- AgentRelated/
`-- ProjectFiles/
```

## Critical Rules

- Create commits on the currently checked out branch at logical checkpoints during multi-step work.
- Keep those commits small, focused, and clearly messaged.
- Do not push unless the user explicitly requests it.

## Folder Responsibilities

- `AgentRelated/` holds stable library-owned assets such as architecture documents, reusable skills, reusable rule files, templates, and guidance that should work across repositories.
- `ProjectFiles/` holds project-specific descriptions, approved codebase-scope preferences, plans, execution notes, and other artifacts created for the current repository.

## Required Navigation Order

1. Read this file first.
2. Read `ARCHITECTURE.md` when you need the layout or ownership model.
3. Read `../ProjectFiles/CodebaseScope.md` and relevant descriptions under `../ProjectFiles/DescriptionFiles/` when the task touches approved codebase roots or you need project-specific file understanding.
4. Read only the relevant rule folders under `AdditionalRules/` for the current task.
5. Read `Templates/README.md` when the task creates durable reusable artifacts or would benefit from a standard document shape.

## Mirrored Project Descriptions

- Project-file descriptions do not belong in this file.
- Approved codebase roots for the current repository belong in `AgentHelper/ProjectFiles/CodebaseScope.md`.
- Real-file descriptions belong under `AgentHelper/ProjectFiles/DescriptionFiles/`.
- When a task touches a project file inside the approved scope, check for the matching description before editing when one exists.
- Verify any reused description against the real file before trusting it as context.
- When no approved codebase scope exists and the task depends on project-file descriptions, inspect the repository, recommend the most likely codebase roots, ask the user to approve that recommendation or provide different folders, and save the approved scope before mapping files.
- Limit description coverage to the approved codebase roots unless the user explicitly asks for broader coverage.
- Exclude dependencies, installed packages, caches, generated output, and agent-support files unless the user explicitly wants them documented.
- When a project file inside the approved scope is created, moved, renamed, or its responsibility changes materially, its matching description should be created or updated.
- Use the real file path relative to the approved codebase root and append `.md` to the filename when saving the description.

Example:

- Approved codebase root: `apps/`
- Real file: `apps/server-nextjs/src/app/layout.tsx`
- Mirrored description file: `AgentHelper/ProjectFiles/DescriptionFiles/server-nextjs/src/app/layout.tsx.md`

## Additional Rules

- Additional rules live under `AdditionalRules/` and are split by topic.
- Load only the topics relevant to the current task.
- Do not load every rule folder unless the task genuinely spans them.

Current rule topics scaffolded in this repository:

- `AdditionalRules/Governance/`
- `AdditionalRules/Git/`
- `AdditionalRules/Skills/`
- `AdditionalRules/Testing/`

Load `AdditionalRules/Governance/ProjectFileDescriptions/` when the task touches files inside approved codebase roots and descriptions may need to be checked, reused, created, or updated.
Load `AdditionalRules/Governance/TemplateFirstArtifacts/` when the task creates or standardizes durable reusable artifacts and should prefer the template library.
Load `AdditionalRules/Testing/LocalTestGate/` when the task changes production code, changes tests in a behavior-affecting way, or needs commit-readiness guidance for local test impact.

## Templates

- Reusable document templates live under `AgentHelper/AgentRelated/Templates/`.
- Prefer the template library when creating recurring artifacts such as context docs, plans, execution logs, verification docs, audits, and codebase maps.
- Check `Templates/README.md` before inventing a new artifact structure.
- If no template fits, create the artifact deliberately and consider whether a new reusable template should be added afterward.

## Skills

- Reusable skills live under `Skills/`.
- Each skill must have its own folder.
- Each reusable skill name must start with `helper-`.
- Do not place multiple skills in one folder.
- Do not place loose skill files directly under `Skills/` unless they are shared index or shared documentation files.
- `AgentRelated/Skills/` is the source of truth for reusable helper skills.
- Mirror reusable helper skills into `.codex/skills/` with `scripts/install-agenthelper-skills.ps1` so the runtime can expose them from the slash picker.
- After creating, editing, renaming, or removing a reusable helper skill, rerun the installer to refresh the generated runtime mirror.
- Current reusable skills:
  - `Skills/helper-map-codebase/`
  - `Skills/helper-improve-skill/`
  - `Skills/helper-qa-agent/`
  - `Skills/helper-sync-codex-skills/`
  - `Skills/helper-test-preferences/`
  - `Skills/helper-test-audit/`
  - `Skills/helper-test-local-cover/`
  - `Skills/helper-test-plan/`
  - `Skills/helper-test-execute-plan/`
