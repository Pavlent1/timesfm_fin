from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Mapping, TypeVar

import psycopg


DEFAULT_POSTGRES_HOST = "127.0.0.1"
DEFAULT_POSTGRES_PORT = 54329
DEFAULT_POSTGRES_DB = "timesfm_fin"
DEFAULT_POSTGRES_USER = "timesfm"
DEFAULT_POSTGRES_PASSWORD = "timesfm_dev"
DEFAULT_POSTGRES_SCHEMA = "market_data"
T = TypeVar("T")


@dataclass(frozen=True)
class PostgresSettings:
    host: str = DEFAULT_POSTGRES_HOST
    port: int = DEFAULT_POSTGRES_PORT
    db_name: str = DEFAULT_POSTGRES_DB
    user: str = DEFAULT_POSTGRES_USER
    password: str = DEFAULT_POSTGRES_PASSWORD

    def with_db(self, db_name: str) -> "PostgresSettings":
        return replace(self, db_name=db_name)

    def conninfo(self) -> str:
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.db_name} "
            f"user={self.user} "
            f"password={self.password}"
        )


def load_postgres_settings(
    env: Mapping[str, str] | None = None,
) -> PostgresSettings:
    source = env or os.environ
    return PostgresSettings(
        host=source.get("POSTGRES_HOST", DEFAULT_POSTGRES_HOST),
        port=int(source.get("POSTGRES_PORT", str(DEFAULT_POSTGRES_PORT))),
        db_name=source.get("POSTGRES_DB", DEFAULT_POSTGRES_DB),
        user=source.get("POSTGRES_USER", DEFAULT_POSTGRES_USER),
        password=source.get("POSTGRES_PASSWORD", DEFAULT_POSTGRES_PASSWORD),
    )


def default_schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "db" / "init" / "001_phase1_schema.sql"


def schema_sql_paths(schema_path: Path | None = None) -> list[Path]:
    anchor_path = schema_path or default_schema_path()
    schema_dir = anchor_path if anchor_path.is_dir() else anchor_path.parent
    sql_paths = sorted(
        path for path in schema_dir.glob("*.sql") if path.is_file()
    )
    if not sql_paths:
        raise ValueError(f"No schema SQL files found under {schema_dir}.")
    return sql_paths


def connect_postgres(
    settings: PostgresSettings | None = None,
    db_name: str | None = None,
    autocommit: bool = False,
) -> psycopg.Connection:
    resolved = settings or load_postgres_settings()
    if db_name is not None:
        resolved = resolved.with_db(db_name)

    conn = psycopg.connect(resolved.conninfo())
    conn.autocommit = autocommit
    return conn


def wait_for_postgres(
    settings: PostgresSettings | None = None,
    timeout_seconds: float = 60.0,
    interval_seconds: float = 1.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with connect_postgres(settings=settings, autocommit=True) as conn:
                conn.execute("SELECT 1")
            return
        except psycopg.Error as exc:
            last_error = exc
            time.sleep(interval_seconds)

    raise RuntimeError(
        "PostgreSQL service did not become ready before the timeout expired."
    ) from last_error


def bootstrap_schema(
    conn: psycopg.Connection,
    schema_path: Path | None = None,
) -> None:
    sql_paths = schema_sql_paths(schema_path)
    with conn.cursor() as cur:
        for sql_path in sql_paths:
            sql_text = sql_path.read_text(encoding="utf-8")
            cur.execute(sql_text)
    conn.commit()


def ensure_asset(
    conn: psycopg.Connection,
    symbol: str,
    asset_type: str = "spot",
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO market_data.assets (symbol, asset_type)
            VALUES (%s, %s)
            ON CONFLICT (symbol) DO UPDATE
            SET asset_type = EXCLUDED.asset_type
            RETURNING asset_id
            """,
            (symbol, asset_type),
        )
        return int(cur.fetchone()[0])


def ensure_series(
    conn: psycopg.Connection,
    symbol: str,
    source_name: str,
    timeframe: str,
    field_name: str = "close_price",
    asset_type: str = "spot",
) -> int:
    asset_id = ensure_asset(conn=conn, symbol=symbol, asset_type=asset_type)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO market_data.series (asset_id, source_name, timeframe, field_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (asset_id, source_name, timeframe, field_name) DO UPDATE
            SET field_name = EXCLUDED.field_name
            RETURNING series_id
            """,
            (asset_id, source_name, timeframe, field_name),
        )
        return int(cur.fetchone()[0])


def start_ingestion_run(
    conn: psycopg.Connection,
    series_id: int,
    source_endpoint: str,
    requested_start_utc: datetime,
    requested_end_utc: datetime,
    notes: dict | None = None,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO market_data.ingestion_runs (
                series_id,
                source_endpoint,
                requested_start_utc,
                requested_end_utc,
                status,
                notes
            )
            VALUES (%s, %s, %s, %s, 'running', %s::jsonb)
            RETURNING ingestion_run_id
            """,
            (
                series_id,
                source_endpoint,
                requested_start_utc,
                requested_end_utc,
                json.dumps(notes or {}),
            ),
        )
        return int(cur.fetchone()[0])


def finalize_ingestion_run(
    conn: psycopg.Connection,
    ingestion_run_id: int,
    actual_start_utc: datetime | None,
    actual_end_utc: datetime | None,
    rows_written: int,
    status: str,
    notes: dict | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE market_data.ingestion_runs
            SET actual_start_utc = %s,
                actual_end_utc = %s,
                rows_written = %s,
                status = %s,
                completed_at_utc = CURRENT_TIMESTAMP,
                notes = notes || %s::jsonb
            WHERE ingestion_run_id = %s
            """,
            (
                actual_start_utc,
                actual_end_utc,
                rows_written,
                status,
                json.dumps(notes or {}),
                ingestion_run_id,
            ),
        )


def mark_ingestion_failed(
    conn: psycopg.Connection,
    ingestion_run_id: int,
    error_message: str,
) -> None:
    finalize_ingestion_run(
        conn=conn,
        ingestion_run_id=ingestion_run_id,
        actual_start_utc=None,
        actual_end_utc=None,
        rows_written=0,
        status="failed",
        notes={"error": error_message},
    )


def batched(values: Iterable[T], batch_size: int) -> Iterator[list[T]]:
    batch: list[T] = []
    for value in values:
        batch.append(value)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def upsert_observations(
    conn: psycopg.Connection,
    series_id: int,
    ingestion_run_id: int,
    observations: Iterable[tuple[datetime, float]],
    batch_size: int = 1000,
) -> int:
    total_rows = 0
    with conn.cursor() as cur:
        for batch in batched(observations, batch_size=batch_size):
            cur.executemany(
                """
                INSERT INTO market_data.observations (
                    series_id,
                    observation_time_utc,
                    close_price,
                    ingestion_run_id
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (series_id, observation_time_utc) DO UPDATE
                SET close_price = EXCLUDED.close_price,
                    ingestion_run_id = EXCLUDED.ingestion_run_id
                """,
                [
                    (series_id, observation_time_utc, close_price, ingestion_run_id)
                    for observation_time_utc, close_price in batch
                ],
            )
            total_rows += len(batch)
    return total_rows
