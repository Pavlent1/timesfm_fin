# `scripts/testing/classify-test-level.mjs`

This Node entrypoint provides a lightweight heuristic recommendation for whether a changed file is best covered with unit, contract, or integration tests. It inspects the target path and file contents, then emits a rationale-rich markdown or JSON recommendation.

The command is designed as an aid for helper-test-local-cover rather than a policy engine. Its side effects are limited to reading the named file from the repository.

Category: test-level classification helper.
