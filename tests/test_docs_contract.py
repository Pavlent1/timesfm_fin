from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_readme_and_db_readme_document_phase1_postgres_workflow() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    db_readme = (REPO_ROOT / "db" / "README.md").read_text(encoding="utf-8")

    required_snippets = [
        "docker compose up -d postgres",
        "python src/bootstrap_postgres.py",
        "python src/postgres_ingest_binance.py",
        "python src/postgres_discover_data.py",
        "python src/postgres_verify_data.py",
        "python src/postgres_materialize_dataset.py",
    ]

    for snippet in required_snippets:
        assert snippet in readme

    assert "Crypto minute backtest with PostgreSQL" in readme
    assert "host.docker.internal" in readme
    assert "backtest_step_stats_vw" in readme
    assert "outputs/crypto_backtest.sqlite" not in readme

    assert "market_data.backtest_runs" in db_readme
    assert "market_data.backtest_windows" in db_readme
    assert "market_data.backtest_prediction_steps" in db_readme
    assert "market_data.backtest_step_stats_vw" in db_readme
    assert "market_data.assets" in db_readme
    assert "market_data.series" in db_readme
    assert "market_data.ingestion_runs" in db_readme
    assert "market_data.observations" in db_readme
    assert "local development trust boundary" in db_readme
    assert "SQLite" not in db_readme
