---
name: helper-test-preferences
description: Learn or update the project's testing policy through short Q/A rounds, resume from saved preferences when present, and keep AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml durable for the rest of the test automation skill suite.
---

# Helper Test Preferences

Learn or update the repository's testing policy through short, high-signal Q/A rounds and save it in `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`.

## Required Workflow

1. Read `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml` first when it exists.
2. When the file exists, summarize the current saved policy before asking new questions:
   - separate confirmed policy from unconfirmed or scaffolded defaults
   - preserve existing sections by default
   - identify deltas only: missing policy, stale policy, repo-state mismatches, or user-requested changes
3. Run `node scripts/testing/discover-test-landscape.mjs --markdown` before asking policy questions so the questions match the repo's actual runners.
4. Start with conservative defaults grounded in the current repo state and the saved preferences, then ask the user to confirm or override only the deltas.
5. Ask short rounds, not one large questionnaire.
6. Cover these topics only when they are missing, stale, inconsistent with repo reality, or explicitly being changed:
   - coverage targets and whether they are advisory or hard
   - preferred unit, integration, and E2E runners
   - given the current repo state, whether Playwright should remain the preferred E2E path and under what constraints or target surface
   - precommit, pull-request, post-push CI, and nightly execution policy
   - mocking rules, especially React hook mocking versus real render paths
   - change policy for bugfixes, refactors, and production-file edits
   - critical flows and intentionally light-tested areas
7. Stop once the saved policy is sufficiently confirmed and actionable for the rest of the test automation skill suite. Do not force every topic into every run.
8. Save partial progress after each round if the conversation is interrupted or the user says to proceed with defaults.
9. Keep the file factual:
   - distinguish confirmed policy from scaffolded defaults
   - preserve previously confirmed fields unless they are being corrected
   - mark conservative defaults as unconfirmed when the user has not explicitly approved them
10. Update `updated_at` only when the policy changes materially, and note what changed in your response.

## Output Standard

- Primary artifact: `AgentHelper/ProjectFiles/TestAutomation/TEST_PREFERENCES.yaml`
- Optional note: a short update in `TEST_BASELINE.md` only when the preference change alters how validation should run

## Guardrails

- Do not reopen already confirmed policy unless it is missing, stale, inconsistent with the repo, or the user wants to change it.
- Do not assume Playwright, hard thresholds, or strict anti-mocking policy unless the user confirms them.
- If the user says "do as you know" or equivalent, keep the defaults conservative and say they remain unconfirmed.
- Do not redesign the repo's mechanical precommit script from this skill alone.
