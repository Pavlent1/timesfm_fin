# `scripts/testing/summarize-test-gaps.mjs`

This Node entrypoint produces a markdown or JSON summary of current testing gaps across the approved codebase roots. It combines the discovered test landscape, coverage-command availability, and a heuristic source-to-test reference map to highlight active blockers and obviously uncovered production files.

The script is meant to support audit refresh work without mutating the codebase. Its main side effects are read-only filesystem inspection and subprocess calls that gather pytest metadata.

Category: test gap summarizer.
