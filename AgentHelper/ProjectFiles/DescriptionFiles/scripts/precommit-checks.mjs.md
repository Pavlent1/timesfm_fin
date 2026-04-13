# `scripts/precommit-checks.mjs`

This Node-based helper is the repository's mechanical pre-commit gate. It resolves the repository root, checks that Docker is reachable because the current full suite starts PostgreSQL through `docker compose`, prefers the checked-in `.venv` Python interpreter when present, and then runs the full `pytest` suite from the repo root so every `git commit` sees the same test command.

The script is designed to be called from the repo-managed Git hook in `.githooks/pre-commit`. Its main side effect is executing the test suite and returning a non-zero exit code when tests fail or when no usable Python-plus-pytest environment can be started.

Category: developer quality gate script.
