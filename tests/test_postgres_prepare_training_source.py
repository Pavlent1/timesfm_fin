from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module

import pytest

from postgres_dataset import (
    ensure_series,
    finalize_ingestion_run,
    start_ingestion_run,
    upsert_observations,
)


pytestmark = pytest.mark.contract


def load_source_module():
    return pytest.importorskip("postgres_prepare_training_source")


def load_verify_module():
    return import_module("postgres_verify_data")


def seed_series(
    conn,
    *,
    symbol: str,
    observations: list[tuple[datetime, float]],
    source_name: str = "binance",
    timeframe: str = "1m",
) -> None:
    series_id = ensure_series(
        conn=conn,
        symbol=symbol,
        source_name=source_name,
        timeframe=timeframe,
    )
    ingestion_run_id = start_ingestion_run(
        conn=conn,
        series_id=series_id,
        source_endpoint="seed://phase-03",
        requested_start_utc=observations[0][0],
        requested_end_utc=observations[-1][0] + timedelta(minutes=1),
        notes={"seeded": True},
    )
    rows_written = upsert_observations(
        conn=conn,
        series_id=series_id,
        ingestion_run_id=ingestion_run_id,
        observations=observations,
    )
    finalize_ingestion_run(
        conn=conn,
        ingestion_run_id=ingestion_run_id,
        actual_start_utc=observations[0][0],
        actual_end_utc=observations[-1][0],
        rows_written=rows_written,
        status="completed",
    )
    conn.commit()


def test_default_source_targets_lock_phase_3_symbol_scope() -> None:
    module = load_source_module()

    assert module.resolve_source_targets() == {
        "BTCUSDT": 40,
        "ETHUSDT": 36,
        "SOLUSDT": 36,
    }
    assert module.resolve_source_targets(["ETHUSDT", "BTCUSDT"]) == {
        "ETHUSDT": 36,
        "BTCUSDT": 40,
    }

    with pytest.raises(ValueError, match="DOGEUSDT"):
        module.resolve_source_targets(["BTCUSDT", "DOGEUSDT"])


def test_btc_readiness_reports_whether_four_month_reserve_can_be_kept() -> None:
    module = load_source_module()
    reference_end = datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc)

    ready = module.evaluate_symbol_readiness(
        {
            "symbol": "BTCUSDT",
            "source_name": "binance",
            "timeframe": "1m",
            "data_start_utc": datetime(2022, 12, 16, 0, 0, tzinfo=timezone.utc),
            "data_end_utc": reference_end,
            "coverage_state": "contiguous",
            "segment_count": 1,
            "segments": [],
            "gaps": [],
            "blocking_gap_count": 0,
            "repairable_gap_count": 0,
        },
        target_months=40,
        end_utc=reference_end,
        reserve_months=4,
    )
    blocked = module.evaluate_symbol_readiness(
        {
            "symbol": "BTCUSDT",
            "source_name": "binance",
            "timeframe": "1m",
            "data_start_utc": datetime(2024, 1, 16, 0, 0, tzinfo=timezone.utc),
            "data_end_utc": reference_end,
            "coverage_state": "contiguous",
            "segment_count": 1,
            "segments": [],
            "gaps": [],
            "blocking_gap_count": 0,
            "repairable_gap_count": 0,
        },
        target_months=40,
        end_utc=reference_end,
        reserve_months=4,
    )

    assert ready["reserve_months"] == 4
    assert ready["reserve_ready"] is True
    assert blocked["reserve_ready"] is False
    assert "reserve" in " ".join(blocked["blocking_reasons"]).lower()


@pytest.mark.integration
def test_integrity_report_distinguishes_contiguous_and_segmented_coverage(
    bootstrapped_postgres_connection,
) -> None:
    verify_module = load_verify_module()
    base = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
    seed_series(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        observations=[
            (base, 70000.0),
            (base + timedelta(minutes=1), 70010.0),
            (base + timedelta(minutes=2), 70020.0),
        ],
    )
    seed_series(
        bootstrapped_postgres_connection,
        symbol="ETHUSDT",
        observations=[
            (base, 3500.0),
            (base + timedelta(minutes=1), 3510.0),
            (base + timedelta(minutes=12), 3525.0),
        ],
    )

    report = verify_module.build_integrity_report(
        bootstrapped_postgres_connection,
        source="binance",
    )
    if "series_details" not in report:
        pytest.skip("03-01 segment-aware integrity details are not implemented yet.")
    by_symbol = {detail["symbol"]: detail for detail in report["series_details"]}

    assert by_symbol["BTCUSDT"]["coverage_state"] == "contiguous"
    assert by_symbol["BTCUSDT"]["segment_count"] == 1
    assert by_symbol["ETHUSDT"]["coverage_state"] == "segmented"
    assert by_symbol["ETHUSDT"]["segment_count"] == 2
    assert by_symbol["ETHUSDT"]["gaps"][0]["missing_minutes"] == 10
    assert by_symbol["ETHUSDT"]["gaps"][0]["severity"] == "blocking"


@pytest.mark.integration
def test_source_readiness_surfaces_missing_symbols_and_blocking_gaps(
    bootstrapped_postgres_connection,
) -> None:
    module = load_source_module()
    base = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)
    seed_series(
        bootstrapped_postgres_connection,
        symbol="BTCUSDT",
        observations=[
            (base, 70000.0),
            (base + timedelta(minutes=1), 70010.0),
            (base + timedelta(minutes=12), 70030.0),
        ],
    )
    seed_series(
        bootstrapped_postgres_connection,
        symbol="ETHUSDT",
        observations=[
            (base, 3500.0),
            (base + timedelta(minutes=1), 3510.0),
            (base + timedelta(minutes=2), 3520.0),
        ],
    )

    report = module.build_source_readiness_report(
        bootstrapped_postgres_connection,
        symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        end_utc=base + timedelta(days=1),
        target_months_by_symbol={
            "BTCUSDT": 0,
            "ETHUSDT": 0,
            "SOLUSDT": 0,
        },
    )

    assert report["ready"] is False
    assert any(finding["symbol"] == "SOLUSDT" for finding in report["blocking_findings"])
    assert any(
        finding["symbol"] == "BTCUSDT" and finding["kind"] == "blocking_gap"
        for finding in report["blocking_findings"]
    )

    with pytest.raises(ValueError, match="SOLUSDT|BTCUSDT"):
        module.assert_training_source_ready(report)


def test_run_source_preparation_reuses_ingest_runner_and_fails_fast(monkeypatch) -> None:
    module = load_source_module()
    calls: list[tuple[str, datetime, datetime]] = []
    fake_conn = object()

    class ConnectionManager:
        def __enter__(self):
            return fake_conn

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_ingest_runner(args, *, now=None):
        calls.append((args.symbol, args.start, args.end))
        return {"status": "completed", "symbol": args.symbol}

    monkeypatch.setattr(module, "connect_postgres", lambda **kwargs: ConnectionManager())
    monkeypatch.setattr(module, "load_postgres_settings", lambda env=None: object())
    monkeypatch.setattr(
        module,
        "build_source_readiness_report",
        lambda conn, **kwargs: {
            "ready": False,
            "blocking_findings": [
                {"symbol": "BTCUSDT", "kind": "blocking_gap", "message": "Gap too large."}
            ],
        },
    )

    args = module.parse_args([])
    args.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    args.strict = True
    args.skip_backfill = False
    args.end = datetime(2026, 4, 16, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="BTCUSDT"):
        module.run_source_preparation(args, ingest_runner=fake_ingest_runner, now=args.end)

    assert [symbol for symbol, _, _ in calls] == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
