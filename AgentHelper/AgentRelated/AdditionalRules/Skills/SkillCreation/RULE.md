# Skill Creation

## Purpose

This rule defines where new reusable skills must be placed.

## When To Load

Load this rule when the task involves creating, reorganizing, or updating a reusable skill.

## Required Placement

- all reusable skills live under `AgentHelper/AgentRelated/Skills/`
- each skill must have its own folder
- all files for one skill stay inside that skill's folder
- `AgentHelper/AgentRelated/Skills/` is the source-of-truth location for reusable helper skills
- the slash-callable runtime mirror for reusable helper skills lives under `.codex/skills/`

## Required Naming

- every reusable skill name must start with the prefix `helper-`
- the skill folder name must exactly match the skill name
- the `name` field in `SKILL.md` must exactly match the folder name
- prompts and references should use the prefixed skill name so agents can find related skills consistently
- the mirrored folder in `.codex/skills/` must use the same skill name as the source folder

## Required Steps

When creating a new skill:

1. choose a hyphen-case skill name that starts with `helper-`
2. create a dedicated folder for that skill under `AgentHelper/AgentRelated/Skills/`
3. place the skill definition file inside that folder
4. place any skill-specific supporting files inside that same folder or its subfolders
5. mirror the skill into `.codex/skills/<skill-name>/` by running `scripts/install-agenthelper-skills.ps1 -Name <skill-name>`
6. verify the mirrored copy contains the current `SKILL.md` and any required support files such as `agents/openai.yaml`, `references/`, `scripts/`, or `assets/`

When updating, renaming, or removing a reusable skill:

1. edit the source-of-truth copy under `AgentHelper/AgentRelated/Skills/`
2. do not hand-edit the generated mirror under `.codex/skills/`
3. rerun `scripts/install-agenthelper-skills.ps1` so the runtime mirror matches the source
4. verify the mirrored runtime copy reflects the latest change

## Do Not

- do not place multiple skills in the same folder
- do not place loose skill files directly in `AgentHelper/AgentRelated/Skills/` unless the file is shared documentation or a shared index
- do not store project-specific artifacts in the reusable skills area
- do not create a reusable skill whose name does not start with `helper-`
- do not treat `.codex/skills/helper-*` as the source of truth for reusable helper skills
- do not leave a reusable helper skill unmirrored after creating or changing it

## Example

```text
AgentHelper/
`-- AgentRelated/
    `-- Skills/
        `-- helper-my-skill/
            |-- SKILL.md
            `-- ...
```
