# Examples

## Example 1: Missing Approved Scope

Situation:

- no `AgentHelper/ProjectFiles/CodebaseScope.md` exists yet
- the repository contains code under `apps/`

Action:

1. inspect the repository tree
2. recommend `apps/` as the codebase root
3. tell the user they can approve with `yes` or `do as you know`, or provide other folders
4. save the approved scope after the user confirms

## Example 2: Missing Description

Situation:

- approved root: `apps/`
- real file exists
- no mirrored description exists yet

Action:

1. read the real file
2. compute the mirrored path under `AgentHelper/ProjectFiles/DescriptionFiles/`
3. create the missing description in that mirrored location as `<real-file-name>.md`

## Example 3: Existing Description Needs Verification

Situation:

- a mirrored description already exists
- the user calls the skill again for the same file or folder

Action:

1. read the real file first
2. compare the description against the real file
3. keep the accurate parts
4. correct stale or missing content
5. update the existing description instead of writing a duplicate

## Example 4: Transfer Old Description Into Mirrored Tree

Situation:

- an older description exists outside the mirrored `AgentHelper/ProjectFiles/DescriptionFiles/` path
- the file still needs a proper mirrored description

Action:

1. read the real file
2. read the older description
3. treat the older description as a draft source only
4. verify it against the real file
5. write the corrected version into the mirrored path

## Example 5: File Changed Too Much

Situation:

- the mirrored description exists
- the real file was heavily refactored
- most of the old description no longer matches

Action:

1. keep the mirrored location
2. replace the stale content with a fresh accurate description
3. do not preserve incorrect legacy claims for the sake of continuity
