---
name: helper-improve-skill
description: Review, improve, and verify another skill's prompt logic, workflow, and expected behavior. Use when Codex needs to audit a skill in a strict sequence of initial analysis, short user Q/A verification, post-Q/A problem analysis, and a brief Top 5 or Top X improvement summary that either asks permission to apply minor changes immediately or offers to create a detailed improvement plan under AgentHelper/ProjectFiles/SkillImprovementPlans.
---

# Helper Improve Skill

Review one target skill at a time and follow the sequence exactly:

1. analyze the current skill
2. run a short Q/A verification with the user
3. analyze again and search for concrete improvements based on the confirmed intent
4. present the top improvements briefly, then branch to either direct minor edits or a detailed plan offer

## Required Workflow

1. Identify the target skill and read its `SKILL.md` plus only the support files needed to understand its workflow.
2. Perform the first analysis pass:
   - explain what the skill currently does
   - explain its current purpose and workflow
   - note likely prompt mistakes, gaps, contradictions, or unclear areas
3. Run a short Q/A verification loop with the user to confirm or correct the intended logic.
4. Perform the second analysis pass after the Q/A:
   - re-evaluate the skill against the user-confirmed intent
   - search for the most important improvements still needed
   - separate minor issues from larger structural problems
5. Present the improvement summary briefly as `Top 5 improvements` or `Top X improvements`, depending on how many meaningful items exist.
6. Branch based on impact:
   - if the changes are minor, ask the user for confirmation to improve the skill on the spot
   - if the changes are larger, offer to create a detailed improvement plan under `AgentHelper/ProjectFiles/SkillImprovementPlans/`
7. If the user approves implementation and the changes affect a reusable helper skill, update the source-of-truth skill under `AgentHelper/AgentRelated/Skills/` and refresh the `.codex/skills/` mirror.

Read [references/workflow.md](references/workflow.md) for the detailed review sequence.
Read [references/question-loop.md](references/question-loop.md) before asking the user to confirm or correct the inferred logic.
Read [references/plan-template.md](references/plan-template.md) when writing an improvement plan.

## Core Rules

### 1. Explain the Existing Logic Before Changing It

State the current purpose, main workflow, and expected outcomes of the target skill in concrete terms before asking the user to validate it.

Do not jump straight to rewriting.

### 2. Keep the Q/A Session Small

Ask short, high-signal questions that the user can answer with:

- `yes`
- `no`
- a short correction

Prefer a few focused questions per round over one long questionnaire.

### 3. Re-Analyze After the User Confirms Intent

Do not treat the first analysis as final.

After the Q/A round, run a second pass that compares:

- current skill behavior
- confirmed intended behavior
- remaining improvement gaps

### 4. Confirm Intent, Not Just Wording

Validate:

- what the skill should optimize for
- what steps are mandatory versus optional
- what artifacts it should create
- when it should ask questions versus make reasonable assumptions
- what counts as a meaningful issue versus a minor polish item

### 5. Present Improvements as a Short Ranked List

After the second analysis, present the improvement summary briefly.

Prefer:

- `Top 5 improvements` when there are many meaningful items
- `Top X improvements` when fewer than 5 items are worth mentioning

Keep the list short, concrete, and behavior-focused.

### 6. Ask for Confirmation on Minor Changes and Offer a Plan for Major Ones

Ask for direct confirmation to implement changes immediately when the remaining issues are minor.

Offer a detailed plan when the review finds meaningful logic changes, missing workflow steps, unclear triggering, broken validation expectations, or larger structural edits.

If the skill already matches the user's intent and only small wording or formatting improvements remain, say so clearly and ask whether to apply those minor edits now.

### 7. Ground Claims in the Real Skill

Base findings on the actual skill files, not assumptions.

If the skill includes scripts, references, assets, or generated metadata, inspect the parts that affect behavior before concluding the skill works correctly.

### 8. Prefer Lightweight Verification First

Use prompt review and user confirmation as the default verification path.

Escalate to forward-testing only when it would materially reduce uncertainty about how the skill behaves in practice.

## Output Standard

If major improvements are required:

- write it to `AgentHelper/ProjectFiles/SkillImprovementPlans/<skill-name>-improvement-YYYY-MM-DD.md`
- keep it concrete and implementation-ready
- separate confirmed intent from inferred recommendations

If only minor improvements are required:

- tell the user the skill is already aligned or close to aligned
- list the minor changes briefly
- ask whether to implement them directly now

## Execution Notes

- Review one skill per pass unless the user explicitly asks for a comparison across multiple skills.
- Prefer quoting the skill's real behavior in your own words instead of copying large prompt sections.
- Keep the visible output sequence strict: first analysis, Q/A, second analysis, brief ranked improvements, then the correct branch for minor or major changes.
- If the target skill is a reusable helper skill, treat `AgentHelper/AgentRelated/Skills/` as the source of truth and do not edit `.codex/skills/` directly.
