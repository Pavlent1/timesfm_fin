from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

import postgres_discover_data
import postgres_ingest_binance
import postgres_materialize_dataset
import postgres_verify_data
from postgres_dataset import PostgresSettings


pytestmark = pytest.mark.contract


class ConnectionManager:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        return False


def test_postgres_ingest_main_prints_summary(monkeypatch, capsys) -> None:
    args = argparse.Namespace(symbol="BTCUSDT", timeframe="1m")
    result = {
        "status": "completed",
        "ingestion_run_id": 17,
        "rows_written": 3,
        "requested_start_utc": datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc),
        "requested_end_utc": datetime(2024, 4, 1, 0, 3, tzinfo=timezone.utc),
        "actual_start_utc": datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc),
        "actual_end_utc": datetime(2024, 4, 1, 0, 2, tzinfo=timezone.utc),
    }

    monkeypatch.setattr(postgres_ingest_binance, "parse_args", lambda: args)
    monkeypatch.setattr(postgres_ingest_binance, "run_ingest", lambda parsed_args: result)

    postgres_ingest_binance.main()

    output = capsys.readouterr().out
    assert "Source: Binance" in output
    assert "Symbol: BTCUSDT" in output
    assert "Timeframe: 1m" in output
    assert "Ingestion run id: 17" in output
    assert "Rows written: 3" in output


def test_postgres_discover_main_builds_settings_and_prints_table(
    monkeypatch,
    capsys,
) -> None:
    args = argparse.Namespace(
        host="db.internal",
        port=54330,
        db_name="finance",
        user="reader",
        password="secret",
        source="binance",
        symbol="BTCUSDT",
        timeframe="1m",
        start=None,
        end=None,
        sort_by="rows",
        descending=True,
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
    expected_frame = pd.DataFrame(
        [
            {
                "source_name": "binance",
                "symbol": "BTCUSDT",
                "timeframe": "1m",
                "row_count": 3,
                "data_start_utc": pd.Timestamp("2024-04-01T00:00:00Z"),
                "data_end_utc": pd.Timestamp("2024-04-01T00:02:00Z"),
                "last_completed_at_utc": pd.Timestamp("2024-04-01T00:03:00Z"),
            }
        ]
    )

    def fake_load_postgres_settings(env):
        calls["env"] = env
        return settings

    def fake_connect_postgres(*, settings, autocommit):
        calls["connect"] = {"settings": settings, "autocommit": autocommit}
        return ConnectionManager(fake_conn)

    def fake_discover_series(conn, **kwargs):
        calls["discover"] = {"conn": conn, **kwargs}
        return expected_frame

    monkeypatch.setattr(postgres_discover_data, "parse_args", lambda: args)
    monkeypatch.setattr(
        postgres_discover_data,
        "load_postgres_settings",
        fake_load_postgres_settings,
    )
    monkeypatch.setattr(postgres_discover_data, "connect_postgres", fake_connect_postgres)
    monkeypatch.setattr(postgres_discover_data, "discover_series", fake_discover_series)

    postgres_discover_data.main()

    assert calls["env"] == {
        "POSTGRES_HOST": "db.internal",
        "POSTGRES_PORT": "54330",
        "POSTGRES_DB": "finance",
        "POSTGRES_USER": "reader",
        "POSTGRES_PASSWORD": "secret",
    }
    assert calls["connect"] == {"settings": settings, "autocommit": True}
    assert calls["discover"] == {
        "conn": fake_conn,
        "source": "binance",
        "symbol": "BTCUSDT",
        "timeframe": "1m",
        "start": None,
        "end": None,
        "sort_by": "rows",
        "descending": True,
    }
    assert (
        capsys.readouterr().out.strip()
        == postgres_discover_data.render_discovery_table(expected_frame).strip()
    )


def test_postgres_verify_main_prints_integrity_report(monkeypatch, capsys) -> None:
    args = argparse.Namespace(
        host="db.internal",
        port=54330,
        db_name="finance",
        user="reader",
        password="secret",
        source="binance",
        symbol="BTCUSDT",
        timeframe="1m",
        start=None,
        end=None,
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
    report = {
        "issue_counts": {"duplicate_timestamps": 0},
        "coverage": pd.DataFrame(),
    }

    def fake_load_postgres_settings(env):
        calls["env"] = env
        return settings

    def fake_connect_postgres(*, settings, autocommit):
        calls["connect"] = {"settings": settings, "autocommit": autocommit}
        return ConnectionManager(fake_conn)

    def fake_build_integrity_report(conn, **kwargs):
        calls["report"] = {"conn": conn, **kwargs}
        return report

    monkeypatch.setattr(postgres_verify_data, "parse_args", lambda: args)
    monkeypatch.setattr(postgres_verify_data, "load_postgres_settings", fake_load_postgres_settings)
    monkeypatch.setattr(postgres_verify_data, "connect_postgres", fake_connect_postgres)
    monkeypatch.setattr(postgres_verify_data, "build_integrity_report", fake_build_integrity_report)
    monkeypatch.setattr(
        postgres_verify_data,
        "render_integrity_report",
        lambda current_report: "Integrity summary:\n- duplicate_timestamps: 0",
    )

    postgres_verify_data.main()

    assert calls["env"] == {
        "POSTGRES_HOST": "db.internal",
        "POSTGRES_PORT": "54330",
        "POSTGRES_DB": "finance",
        "POSTGRES_USER": "reader",
        "POSTGRES_PASSWORD": "secret",
    }
    assert calls["connect"] == {"settings": settings, "autocommit": True}
    assert calls["report"] == {
        "conn": fake_conn,
        "source": "binance",
        "symbol": "BTCUSDT",
        "timeframe": "1m",
        "start": None,
        "end": None,
    }
    assert capsys.readouterr().out.strip() == "Integrity summary:\n- duplicate_timestamps: 0"


@pytest.mark.parametrize("mode", ["series_csv", "training_matrix"])
def test_postgres_materialize_main_routes_output_mode(
    monkeypatch,
    capsys,
    tmp_path,
    mode: str,
) -> None:
    output_csv = tmp_path / f"{mode}.csv"
    args = argparse.Namespace(
        host="db.internal",
        port=54330,
        db_name="finance",
        user="reader",
        password="secret",
        source="binance",
        symbol="BTCUSDT",
        timeframe="1m",
        start=None,
        end=None,
        mode=mode,
        output_csv=output_csv,
    )
    settings = PostgresSettings(
        host=args.host,
        port=args.port,
        db_name=args.db_name,
        user=args.user,
        password=args.password,
    )
    fake_conn = object()
    observed: dict[str, object] = {}
    loaded_frame = pd.DataFrame(
        [
            {
                "source_name": "binance",
                "symbol": "BTCUSDT",
                "timeframe": "1m",
                "observation_time_utc": pd.Timestamp("2024-04-01T00:00:00Z"),
                "close_price": 70000.0,
                "series_label": "binance__BTCUSDT__1m",
            }
        ]
    )
    output_frame = pd.DataFrame([{"value": 1.0}])

    def fake_connect_postgres(*, settings, autocommit):
        observed["connect"] = {"settings": settings, "autocommit": autocommit}
        return ConnectionManager(fake_conn)

    def fake_load_matching_observations(conn, **kwargs):
        observed["load"] = {"conn": conn, **kwargs}
        return loaded_frame

    def fake_materialize_series_csv(frame):
        observed["mode"] = "series_csv"
        observed["frame"] = frame
        return output_frame

    def fake_materialize_training_matrix(frame):
        observed["mode"] = "training_matrix"
        observed["frame"] = frame
        return output_frame

    def fake_write_materialized_csv(frame, destination):
        observed["write"] = {"frame": frame, "destination": destination}

    monkeypatch.setattr(postgres_materialize_dataset, "parse_args", lambda: args)
    monkeypatch.setattr(
        postgres_materialize_dataset,
        "load_postgres_settings",
        lambda env: settings,
    )
    monkeypatch.setattr(
        postgres_materialize_dataset,
        "connect_postgres",
        fake_connect_postgres,
    )
    monkeypatch.setattr(
        postgres_materialize_dataset,
        "load_matching_observations",
        fake_load_matching_observations,
    )
    monkeypatch.setattr(
        postgres_materialize_dataset,
        "materialize_series_csv",
        fake_materialize_series_csv,
    )
    monkeypatch.setattr(
        postgres_materialize_dataset,
        "materialize_training_matrix",
        fake_materialize_training_matrix,
    )
    monkeypatch.setattr(
        postgres_materialize_dataset,
        "write_materialized_csv",
        fake_write_materialized_csv,
    )

    postgres_materialize_dataset.main()

    assert observed["connect"] == {"settings": settings, "autocommit": True}
    assert observed["load"] == {
        "conn": fake_conn,
        "source": "binance",
        "symbol": "BTCUSDT",
        "timeframe": "1m",
        "start": None,
        "end": None,
    }
    assert observed["mode"] == mode
    assert observed["frame"] is loaded_frame
    assert observed["write"] == {"frame": output_frame, "destination": output_csv}
    assert capsys.readouterr().out.strip() == (
        f"Mode: {mode}\nRows: 1\nColumns: 1\nSaved to: {output_csv}"
    )
