# Rule Writing

## Purpose

This rule defines how to add new rules to `AgentHelper`.

## Placement

When creating a new rule:

1. choose the narrowest topic folder under `AgentHelper/AgentRelated/AdditionalRules/`
2. create a dedicated folder for the rule inside that topic
3. place the rule content inside that rule folder

## Writing Standard

Each new rule should state:

- what the rule is for
- when the rule should be loaded
- what an agent must do
- what an agent must not do
- at least one concrete example when that helps remove ambiguity

## Scope Discipline

- keep rules topic-specific
- do not mix unrelated guidance into one rule
- prefer small rules that agents can load selectively
- create a new topic folder only when an existing topic would be a poor fit

## Required Follow-Up

When a new rule is added:

- make sure it lives in the correct topic folder
- update any nearby topic index or README if needed
- mention the rule from the main `AGENTS.md` only if it changes entry-point behavior
