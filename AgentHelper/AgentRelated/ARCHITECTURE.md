# AgentHelper Architecture

## Purpose

`AgentHelper` is a reusable agent-support library intended to be portable between repositories.

Its main design rule is to separate:

- reusable library-owned assets
- project-specific working artifacts

## Root Layout

```text
AgentHelper/
|-- AgentRelated/
`-- ProjectFiles/
```

## AgentRelated

`AgentRelated/` is the stable library area.

Use this area for assets that should remain reusable across projects:

- `AGENTS.template.md`
- architecture documents
- reusable skills
- reusable templates
- reusable prompts
- topic-scoped additional rules

Expected structure:

```text
AgentHelper/
`-- AgentRelated/
    |-- AGENTS.template.md
    |-- ARCHITECTURE.md
    |-- Skills/
    |-- Templates/
    `-- AdditionalRules/
```

## ProjectFiles

`ProjectFiles/` is the project-owned area.

Use this area for assets created because `AgentHelper` is being used inside one specific repository:

- approved codebase-scope preferences
- mirrored project file descriptions
- project context documents
- plans
- execution notes
- repository-specific artifacts

Recommended project-owned layout:

```text
AgentHelper/
`-- ProjectFiles/
    |-- CodebaseScope.md
    `-- DescriptionFiles/
```

`CodebaseScope.md` stores the user-approved folders that count as the codebase for description work.

`DescriptionFiles/` stores descriptions for real repository files that belong to the approved codebase scope.

For a single approved root, mirror paths relative to that root. For multiple approved roots, preserve separate top-level trees to avoid collisions.

Example:

- Approved codebase root: `apps/`
- Real file: `apps/server-nextjs/src/app/layout.tsx`
- Mirrored description file: `AgentHelper/ProjectFiles/DescriptionFiles/server-nextjs/src/app/layout.tsx.md`

## Additional Rules Model

Additional rules are split by topic so an agent can load only what is relevant.

Expected pattern:

```text
AgentHelper/
`-- AgentRelated/
    `-- AdditionalRules/
        |-- Governance/
        |-- Skills/
        `-- ...
```

Each topic can contain one or more focused rule folders.

## Skills Model

Reusable skills live under `AgentRelated/Skills/`.

Rules:

- each skill must have its own folder
- a skill's files stay inside that skill's folder
- the skills root should not become a dump of loose files
- `AgentRelated/Skills/` is the source-of-truth library area for reusable helper skills
- `.codex/skills/` is the repo-local runtime mirror for slash-callable copies of reusable helper skills
- refresh `.codex/skills/` from the source tree with `scripts/install-agenthelper-skills.ps1` after helper skill creation or edits

## Templates Model

Reusable templates live under `AgentRelated/Templates/`.

Rules:

- templates belong in the reusable library area, not under `ProjectFiles/`
- organize templates by source or domain so provenance stays obvious
- prefer reusing an existing template when creating durable artifacts
- document the intended use of each template family so future agents do not guess
- preserve imported upstream templates in a namespaced layout when copying them from another library

Current template library:

- `Templates/README.md`
- `Templates/gsd/get-shit-done/`
- `Templates/gsd/feature-workflow/`

## Entry Files

- `AGENTS.md` at the repository root: active auto-discovered instruction entrypoint for this repository
- `AgentHelper/AgentRelated/AGENTS.template.md`: reusable helper-library instruction template/reference copy
- `AgentHelper/AgentRelated/ARCHITECTURE.md`: stable layout and ownership reference
- `AgentHelper/ProjectFiles/CodebaseScope.md`: approved codebase roots for description mapping
