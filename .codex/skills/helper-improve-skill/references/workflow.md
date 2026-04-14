# Workflow

## 1. Load the Target Skill

Read:

- the target `SKILL.md`
- `agents/openai.yaml` when it exists
- only the support files that materially affect the skill's behavior

Capture:

- the claimed purpose
- triggering language
- required workflow
- artifacts the skill creates or updates
- validation expectations

## 2. First Analysis Pass

Summarize:

- what problem the skill solves
- what sequence it asks the agent to follow
- what assumptions it makes
- where it may confuse or mislead the agent

Look for issues such as:

- vague or overloaded triggering language
- hidden assumptions not stated in the workflow
- missing validation or verification steps
- conflicting instructions between frontmatter, body, and references
- workflow steps that are too rigid or too loose
- artifacts or folders mentioned without a naming convention
- prompt text that encourages the wrong tradeoff

## 3. Run the Verification Loop

Present the inferred logic back to the user in a compact form, then ask a short round of confirmation questions.

Good examples:

- `Should this skill always ask at least one confirmation round before editing the target skill?`
- `Should minor wording fixes skip plan creation?`
- `Should the plan always be saved under AgentHelper/ProjectFiles/SkillImprovementPlans?`

Bad examples:

- long multi-part questions
- abstract questions without a concrete behavior attached
- questions the user can only answer by rereading the whole skill

If the user corrects the intended logic, update your understanding and ask a follow-up round only where uncertainty remains.

## 4. Second Analysis Pass

After the Q/A, analyze again.

Compare:

- what the skill currently does
- what the user confirmed it should do
- what the most important remaining gaps are

Separate the findings into:

- minor improvements
- material improvements

## 5. Present Top Improvements

Explain the improvement opportunities briefly as:

- `Top 5 improvements` when there are at least 5 meaningful items
- `Top X improvements` when there are fewer

Good output traits:

- short
- concrete
- prioritized
- tied to behavior, not vague taste

## 6. Decide Between Plan and Direct Edits

Write a plan when at least one of these is true:

- the target workflow needs structural changes
- the trigger description is materially wrong
- the skill is missing required files or artifact conventions
- the verification loop changes the intended logic in a non-trivial way
- the skill needs broader refactoring or new supporting resources

Skip the plan and offer direct implementation when:

- the target logic is already aligned
- only small wording, ordering, or metadata changes are needed
- the review produces no meaningful change in behavior

For minor changes, explicitly ask the user if the skill should be improved on the spot.

For larger changes, explicitly offer to create the detailed plan.

## 7. Write the Plan When Needed

Use the template in [plan-template.md](plan-template.md).

Save the plan at:

- `AgentHelper/ProjectFiles/SkillImprovementPlans/<skill-name>-improvement-YYYY-MM-DD.md`

If a plan for the same skill already exists for the same date, update it in place unless the user asks for a separate variant.

## 8. Recommend Next Action

End with one clear next step:

- implement the planned changes
- apply the minor edits directly
- run forward-testing on a representative task if uncertainty remains
