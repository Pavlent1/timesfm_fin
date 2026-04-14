# Question Loop

Use short confirmation rounds between the first and second analysis passes to verify the intended behavior of the target skill.

## Rules

- Ask at most 3 to 5 questions per round.
- Make each question about one concrete behavior.
- Prefer yes-or-no questions with room for a short correction.
- Stop asking once the intended logic is stable enough to act on.
- Do not ask questions whose answers are already explicit in the user's latest message.
- Treat the answers as inputs for the second analysis pass, not as the final output.

## Good Question Types

- purpose confirmation
- mandatory versus optional step confirmation
- artifact location confirmation
- threshold confirmation for "minor change" versus "material change"
- validation expectation confirmation

## Example Prompts

- `My current reading is that this skill should first analyze the target skill, then ask a short confirmation round before making any changes. Is that correct?`
- `Should the skill write a plan only when the changes are meaningful, and otherwise offer direct minor edits?`
- `Should the improvement plan be stored under AgentHelper/ProjectFiles/SkillImprovementPlans?`

## Avoid

- asking everything in one message when only one uncertainty matters
- asking the user to restate the whole skill idea
- forcing long-form answers when a short correction would do
- treating early assumptions as final without confirmation
