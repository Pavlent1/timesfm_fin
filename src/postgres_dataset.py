from __future__ import annotations

import os
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping

import psycopg


DEFAULT_POSTGRES_HOST = "127.0.0.1"
DEFAULT_POSTGRES_PORT = 54329
DEFAULT_POSTGRES_DB = "timesfm_fin"
DEFAULT_POSTGRES_USER = "timesfm"
DEFAULT_POSTGRES_PASSWORD = "timesfm_dev"
DEFAULT_POSTGRES_SCHEMA = "market_data"


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
    sql_path = schema_path or default_schema_path()
    sql_text = sql_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql_text)
    conn.commit()
