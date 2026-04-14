from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bootstrap_postgres
from postgres_dataset import PostgresSettings


class ConnectionManager:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        return False


def test_parse_args_uses_loaded_postgres_defaults(monkeypatch) -> None:
    defaults = PostgresSettings(
        host="db.internal",
        port=6543,
        db_name="finance",
        user="reader",
        password="secret",
    )
    schema_path = Path("db/init/test-schema.sql")

    monkeypatch.setattr(bootstrap_postgres, "load_postgres_settings", lambda: defaults)
    monkeypatch.setattr(bootstrap_postgres, "default_schema_path", lambda: schema_path)
    monkeypatch.setattr(sys, "argv", ["bootstrap_postgres.py"])

    args = bootstrap_postgres.parse_args()

    assert args.host == defaults.host
    assert args.port == defaults.port
    assert args.db_name == defaults.db_name
    assert args.user == defaults.user
    assert args.password == defaults.password
    assert args.schema_file == schema_path
    assert args.wait_seconds == 60.0
    assert args.skip_wait is False


def test_parse_args_accepts_skip_wait_and_schema_override(monkeypatch) -> None:
    schema_path = Path("db/init/custom-schema.sql")

    monkeypatch.setattr(bootstrap_postgres, "load_postgres_settings", PostgresSettings)
    monkeypatch.setattr(sys, "argv", [
        "bootstrap_postgres.py",
        "--host",
        "db.service",
        "--port",
        "54330",
        "--db-name",
        "analytics",
        "--user",
        "operator",
        "--password",
        "pw",
        "--schema-file",
        str(schema_path),
        "--wait-seconds",
        "5.5",
        "--skip-wait",
    ])

    args = bootstrap_postgres.parse_args()

    assert args.host == "db.service"
    assert args.port == 54_330
    assert args.db_name == "analytics"
    assert args.user == "operator"
    assert args.password == "pw"
    assert args.schema_file == schema_path
    assert args.wait_seconds == 5.5
    assert args.skip_wait is True


def test_main_waits_then_bootstraps_schema(monkeypatch, capsys) -> None:
    args = argparse.Namespace(
        host="db.internal",
        port=54329,
        db_name="timesfm_fin",
        user="timesfm",
        password="timesfm_dev",
        schema_file=Path("db/init/001_phase1_schema.sql"),
        wait_seconds=12.5,
        skip_wait=False,
    )
    settings = PostgresSettings(
        host=args.host,
        port=args.port,
        db_name=args.db_name,
        user=args.user,
        password=args.password,
    )
    fake_conn = object()
    calls: dict[str, object] = {}

    def fake_connect_postgres(*, settings, autocommit):
        calls["connect"] = {"settings": settings, "autocommit": autocommit}
        return ConnectionManager(fake_conn)

    def fake_wait_for_postgres(*, settings, timeout_seconds):
        calls["wait"] = {"settings": settings, "timeout_seconds": timeout_seconds}

    def fake_bootstrap_schema(*, conn, schema_path):
        calls["bootstrap"] = {"conn": conn, "schema_path": schema_path}

    monkeypatch.setattr(bootstrap_postgres, "parse_args", lambda: args)
    monkeypatch.setattr(bootstrap_postgres, "build_settings", lambda parsed_args: settings)
    monkeypatch.setattr(bootstrap_postgres, "wait_for_postgres", fake_wait_for_postgres)
    monkeypatch.setattr(bootstrap_postgres, "connect_postgres", fake_connect_postgres)
    monkeypatch.setattr(bootstrap_postgres, "bootstrap_schema", fake_bootstrap_schema)

    bootstrap_postgres.main()

    assert calls["wait"] == {"settings": settings, "timeout_seconds": 12.5}
    assert calls["connect"] == {"settings": settings, "autocommit": False}
    assert calls["bootstrap"] == {
        "conn": fake_conn,
        "schema_path": args.schema_file,
    }
    assert (
        capsys.readouterr().out.strip()
        == f"Applied schema {args.schema_file} to db.internal:54329/timesfm_fin."
    )


def test_main_skips_wait_when_requested(monkeypatch, capsys) -> None:
    args = argparse.Namespace(
        host="db.internal",
        port=54329,
        db_name="timesfm_fin",
        user="timesfm",
        password="timesfm_dev",
        schema_file=Path("db/init/custom.sql"),
        wait_seconds=30.0,
        skip_wait=True,
    )
    settings = PostgresSettings(
        host=args.host,
        port=args.port,
        db_name=args.db_name,
        user=args.user,
        password=args.password,
    )
    fake_conn = object()
    calls: dict[str, object] = {}

    def fake_connect_postgres(*, settings, autocommit):
        calls["connect"] = {"settings": settings, "autocommit": autocommit}
        return ConnectionManager(fake_conn)

    def fail_wait_for_postgres(**kwargs):
        raise AssertionError("wait_for_postgres should not be called when --skip-wait is set")

    def fake_bootstrap_schema(*, conn, schema_path):
        calls["bootstrap"] = {"conn": conn, "schema_path": schema_path}

    monkeypatch.setattr(bootstrap_postgres, "parse_args", lambda: args)
    monkeypatch.setattr(bootstrap_postgres, "build_settings", lambda parsed_args: settings)
    monkeypatch.setattr(bootstrap_postgres, "wait_for_postgres", fail_wait_for_postgres)
    monkeypatch.setattr(bootstrap_postgres, "connect_postgres", fake_connect_postgres)
    monkeypatch.setattr(bootstrap_postgres, "bootstrap_schema", fake_bootstrap_schema)

    bootstrap_postgres.main()

    assert "wait" not in calls
    assert calls["connect"] == {"settings": settings, "autocommit": False}
    assert calls["bootstrap"] == {
        "conn": fake_conn,
        "schema_path": args.schema_file,
    }
    assert (
        capsys.readouterr().out.strip()
        == f"Applied schema {args.schema_file} to db.internal:54329/timesfm_fin."
    )
