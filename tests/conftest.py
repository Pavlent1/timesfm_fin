from __future__ import annotations

import subprocess
import sys
import time
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
import pytest
from psycopg import sql


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from postgres_dataset import bootstrap_schema, connect_postgres, load_postgres_settings


DOCKER_FIXTURES = {
    "repo_postgres_service",
    "postgres_test_database",
    "bootstrapped_postgres_connection",
    "dataset_factory",
}


def run_checked_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="session")
def repo_postgres_service():
    run_checked_command("docker", "compose", "up", "-d", "postgres")

    settings = load_postgres_settings()
    deadline = time.monotonic() + 60.0
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with connect_postgres(settings=settings, autocommit=True) as conn:
                conn.execute("SELECT 1")
            return settings
        except psycopg.Error as exc:
            last_error = exc
            time.sleep(1.0)

    raise RuntimeError("Compose-managed PostgreSQL never became ready.") from last_error


@pytest.fixture()
def postgres_test_database(repo_postgres_service):
    admin_settings = replace(repo_postgres_service, db_name="postgres")
    database_name = f"phase1_{uuid.uuid4().hex}"

    with connect_postgres(settings=admin_settings, autocommit=True) as conn:
        conn.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )

    try:
        yield replace(repo_postgres_service, db_name=database_name)
    finally:
        with connect_postgres(settings=admin_settings, autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )


@pytest.fixture()
def bootstrapped_postgres_connection(postgres_test_database):
    conn = connect_postgres(settings=postgres_test_database, autocommit=False)
    try:
        bootstrap_schema(conn)
        yield conn
    finally:
        conn.close()


class DatasetFactory:
    def __init__(self, conn: psycopg.Connection):
        self.conn = conn

    def ensure_asset(self, symbol: str = "BTCUSDT", asset_type: str = "spot") -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO market_data.assets (symbol, asset_type)
                VALUES (%s, %s)
                ON CONFLICT (symbol) DO UPDATE SET asset_type = EXCLUDED.asset_type
                RETURNING asset_id
                """,
                (symbol, asset_type),
            )
            asset_id = int(cur.fetchone()[0])
        self.conn.commit()
        return asset_id

    def ensure_series(
        self,
        symbol: str = "BTCUSDT",
        source_name: str = "binance",
        timeframe: str = "1m",
        field_name: str = "close_price",
    ) -> int:
        asset_id = self.ensure_asset(symbol=symbol)
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO market_data.series (asset_id, source_name, timeframe, field_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (asset_id, source_name, timeframe, field_name)
                DO UPDATE SET field_name = EXCLUDED.field_name
                RETURNING series_id
                """,
                (asset_id, source_name, timeframe, field_name),
            )
            series_id = int(cur.fetchone()[0])
        self.conn.commit()
        return series_id

    def create_ingestion_run(
        self,
        series_id: int,
        source_endpoint: str = "https://api.binance.com/api/v3/klines",
        requested_start_utc: datetime | None = None,
        requested_end_utc: datetime | None = None,
        rows_written: int = 0,
        status: str = "completed",
    ) -> int:
        start_utc = requested_start_utc or datetime.now(timezone.utc) - timedelta(days=1)
        end_utc = requested_end_utc or datetime.now(timezone.utc)
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO market_data.ingestion_runs (
                    series_id,
                    source_endpoint,
                    requested_start_utc,
                    requested_end_utc,
                    actual_start_utc,
                    actual_end_utc,
                    rows_written,
                    status,
                    completed_at_utc
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING ingestion_run_id
                """,
                (
                    series_id,
                    source_endpoint,
                    start_utc,
                    end_utc,
                    start_utc,
                    end_utc,
                    rows_written,
                    status,
                ),
            )
            ingestion_run_id = int(cur.fetchone()[0])
        self.conn.commit()
        return ingestion_run_id


@pytest.fixture()
def dataset_factory(bootstrapped_postgres_connection):
    return DatasetFactory(bootstrapped_postgres_connection)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        node_path = str(item.path).replace("\\", "/")

        if any(fixture_name in item.fixturenames for fixture_name in DOCKER_FIXTURES):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.docker)
            continue

        if node_path.endswith("tests/test_docs_contract.py"):
            item.add_marker(pytest.mark.contract)
            continue

        item.add_marker(pytest.mark.unit)
