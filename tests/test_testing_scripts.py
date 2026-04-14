from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_node_script(*args: str) -> str:
    completed = subprocess.run(
        ["node", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_discover_test_landscape_reports_pytest_and_markers() -> None:
    output = run_node_script("scripts/testing/discover-test-landscape.mjs", "--markdown")

    assert "# Test Landscape" in output
    assert "pytest" in output
    assert "`docker`" in output


def test_measure_coverage_reports_unavailable_without_pytest_cov() -> None:
    output = run_node_script("scripts/testing/measure-coverage.mjs", "--markdown")

    assert "# Coverage Status" in output
    assert "`unavailable`" in output
    assert "pytest-cov is not installed" in output


def test_summarize_test_gaps_highlights_known_missing_coverage() -> None:
    output = run_node_script("scripts/testing/summarize-test-gaps.mjs", "--markdown")

    assert "# Test Gap Summary" in output
    assert "## Missing Direct Coverage" in output
    assert "`src/binance_market_data.py`" not in output
    assert "`src/bootstrap_postgres.py`" not in output
    assert "`src/crypto_minute_backtest.py`" not in output
    assert "`src/evaluation.py`" in output


def test_find_affected_tests_reports_markdown_output() -> None:
    output = run_node_script("scripts/testing/find-affected-tests.mjs", "--markdown")

    assert "# Affected Tests" in output
    assert "No changed files detected." in output or "Changed Files" in output


def test_classify_test_level_recommends_unit_for_testing_helpers() -> None:
    output = run_node_script(
        "scripts/testing/classify-test-level.mjs",
        "--source",
        "scripts/testing/discover-test-landscape.mjs",
        "--markdown",
    )

    assert "# Test Level Classification" in output
    assert "`unit`" in output
