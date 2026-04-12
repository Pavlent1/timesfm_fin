# Workflow

## Purpose

Use this workflow when the task is to map approved codebase files into `AgentHelper/ProjectFiles/DescriptionFiles/`, create missing descriptions, or verify and correct existing descriptions.

## Step 1: Load or Establish Codebase Scope

Read `AgentHelper/ProjectFiles/CodebaseScope.md` first when it exists.

If no approved scope exists:

- inspect the repository tree
- recommend the most likely codebase folders
- tell the user they can approve with `yes`, `do as you know`, or a similar short confirmation
- let the user override the recommendation with explicit folders
- save the approved scope before mapping files

Prefer the narrowest scope that still covers the requested work.

## Step 2: Discover Real Files

List the files inside scope from the real repository tree.

Do not step outside the approved codebase roots unless the user explicitly broadens the scope.

Ignore generated folders, dependencies, installed packages, and agent-support folders unless the user explicitly wants them documented.

Typical exclusions:

- `node_modules/`
- `.venv/`
- build output
- caches
- generated artifacts that do not need agent-facing descriptions
- `AgentHelper/`
- `.codex/`
- `.claude/`
- `.planning/`

## Step 3: Compute Mirrored Targets

For each real file, compute the matching mirrored location under `AgentHelper/ProjectFiles/DescriptionFiles/`.

Rule:

- if there is one approved root, mirror the path relative to that root
- if there are multiple approved roots, keep a top-level folder for each approved root
- append `.md` to the real filename

Example:

- approved root: `apps/`
- real file: `apps/server-nextjs/src/app/layout.tsx`
- mirrored file: `AgentHelper/ProjectFiles/DescriptionFiles/server-nextjs/src/app/layout.tsx.md`

## Step 4: Check for Existing Descriptions

Before writing anything new:

- look for an existing mirrored description in the matching mirrored path
- look for older notes or prior descriptions that may need to be transferred
- inspect nearby mirrored files to follow the existing local convention

## Step 5: Read the Real File

Always inspect the real file before trusting prior documentation.

Focus on:

- exported functions, classes, or components
- file purpose
- side effects
- important imports
- important consumers or routes
- configuration or environment usage

## Step 6: Verify Existing Descriptions

If a description already exists:

- compare every key claim against the current real file
- keep only the verified parts
- mark stale assumptions for correction
- add missing responsibilities that are now present in the file

Do not keep legacy wording when the file behavior has changed.

## Step 7: Decide Action

Use this decision rule:

- no description exists: create one
- description exists and is mostly correct: update in place
- description exists but is partly stale: correct and expand it
- description exists but is badly wrong or unusable: rewrite it in the same mirrored location

## Step 8: Write the Description

Write for future agent navigation, not for marketing.

Prefer:

- direct purpose statements
- concrete responsibilities
- notable interactions
- clear limits

Avoid:

- vague summaries
- guessing hidden behavior
- repeating filenames without explaining behavior

## Step 9: Verify the Finished Description

Before finishing, make sure:

- the mirrored path is correct
- the file lives inside the approved codebase scope
- the description matches the current file
- stale claims were removed
- the wording is specific enough to guide later work

## Step 10: Report Results

When closing the task, summarize:

- which codebase scope was used
- which files were mapped
- which descriptions were created
- which descriptions were verified and kept
- which descriptions were corrected
- any uncertain areas that still need human or deeper code review
