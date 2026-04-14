# `scripts/testing/_shared.mjs`

This shared ESM helper module centralizes the repo-root path resolution, CLI argument parsing, subprocess capture, and test-landscape heuristics used by the `scripts/testing/*.mjs` commands. It is the common plumbing for Wave 1 test-tooling scripts rather than a user-facing entrypoint.

The module's main side effects are spawning read-only subprocesses such as `pytest --collect-only` and `git status --porcelain` from the repository root. It also formats the markdown payloads consumed by the helper-test workflows.

Category: test automation support library.
