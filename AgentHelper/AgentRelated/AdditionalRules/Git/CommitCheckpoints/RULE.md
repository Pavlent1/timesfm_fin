# Commit Checkpoints

## Purpose

This rule defines the default git commit behavior for AgentHelper-guided work.

## When To Load

Load this rule when the task involves making repository changes that may need one or more commits.

## Required Behavior

- create commits on the currently checked out branch at logical checkpoints during multi-step work
- keep each commit small and focused on one coherent slice of work
- write clear commit messages that describe the actual change
- do not push unless the user explicitly requests it

## Checkpoint Guidance

Good checkpoint commits usually happen when:

- one self-contained documentation change is complete
- one rule or skill change is complete
- one implementation slice is complete and locally verified as far as practical
- a longer task reaches a stable intermediate state that would be useful to resume from

Avoid checkpoint commits when:

- the work is still in a broken half-state unless that state is the safest recoverable boundary
- unrelated changes are mixed together and should be split first

## Do Not

- do not wait until the entire multi-step task is finished if earlier logical checkpoints exist
- do not create one large mixed commit when the work naturally splits into smaller coherent commits
- do not push after committing unless the user explicitly asks for a push

## Message Standard

Commit messages should be short, direct, and specific to the completed checkpoint.

Prefer messages that describe the actual completed change, for example:

- `Add helper-map-codebase skill`
- `Enforce helper- prefix for reusable skills`
- `Document commit checkpoint rule in AgentHelper`
