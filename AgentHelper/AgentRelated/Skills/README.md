# Skills

This folder contains reusable `AgentHelper` skills.

Rules:

- each skill must have its own folder
- each reusable skill name must start with `helper-`
- all files for a skill stay inside that skill's folder
- do not place loose skill files here unless they are shared documentation or a shared index
- this folder is the source of truth for reusable helper skills
- mirror helper skills into `.codex/skills/` with `scripts/install-agenthelper-skills.ps1`
- rerun the installer after helper skill changes so the runtime mirror stays current
- `helper-improve-skill/`: audits another skill, verifies intended logic with the user through short Q/A rounds, and either writes a concrete improvement plan or recommends direct minor edits.
- `helper-map-codebase/`: maps approved codebase files into the description tree, persists the approved scope, and verifies or corrects existing file descriptions.
- `helper-qa-agent/`: acts as the single QA entrypoint that routes between test preferences, audit, planning, local coverage, execution, and planner-facing handoff work.
- `helper-sync-codex-skills/`: refreshes the repo-local `.codex/skills` mirror from the AgentHelper source tree.
- `helper-test-preferences/`: learns and saves project testing policy for the rest of the reusable test automation suite.
- `helper-test-audit/`: audits existing unit, integration, and E2E coverage from real repo evidence, records missing-test gaps, and writes the detailed audit plus measured baseline artifacts.
- `helper-test-local-cover/`: adds or improves the smallest correct tests for changed code without widening into a repo-wide test campaign.
- `helper-test-plan/`: builds a phased repo-wide automated testing roadmap from saved preferences and measured gaps.
- `helper-test-execute-plan/`: executes an already prepared testing roadmap wave by wave and keeps execution notes current.
