# `scripts/testing/discover-test-landscape.mjs`

This Node entrypoint inventories the current test stack for the repository. It uses the shared helper module to detect pytest availability, registered markers, helper-script presence, and the current collected test count, then emits either JSON or markdown.

The script is intended to satisfy the helper-test-audit and helper-test-plan workflows that need a durable, repo-owned discovery command instead of manual inspection. Its main side effect is read-only subprocess execution against the local Python environment.

Category: test discovery command.
