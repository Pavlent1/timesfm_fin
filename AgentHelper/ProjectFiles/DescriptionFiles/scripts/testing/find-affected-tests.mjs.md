# `scripts/testing/find-affected-tests.mjs`

This Node entrypoint maps the current git working-tree changes to likely related pytest files. It reads `git status --porcelain`, applies simple filename and content heuristics, and emits a compact markdown or JSON list of changed paths plus candidate tests.

The script exists to support helper-test-local-cover when the user does not name a scope explicitly. It is read-only apart from invoking Git to inspect the working tree.

Category: changed-file to test-map helper.
