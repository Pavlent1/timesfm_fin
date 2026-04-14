# `scripts/testing/measure-coverage.mjs`

This Node entrypoint reports whether the repository currently has a runnable coverage command. In the current Wave 1 implementation it checks the repo-managed Python environment for `pytest-cov` and reports coverage as available or unavailable, rather than silently failing with a missing-module error.

The script is a conservative coverage-status probe for the helper-test workflows. Its main side effect is a short Python subprocess used to check plugin availability.

Category: test coverage status command.
