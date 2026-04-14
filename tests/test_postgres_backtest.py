from __future__ import annotations

import math
from datetime import datetime
from importlib import import_module

from postgres_dataset import bootstrap_schema, connect_postgres


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_postgres_backtest_module():
    return import_module("postgres_backtest")


def build_step_rows(
    run_id: int,
    window_id: int,
    *,
    last_input_close: float,
    step_specs: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for step_index, spec in enumerate(step_specs):
        rows.append(
            {
                "run_id": run_id,
                "window_id": window_id,
                "step_index": step_index,
                "target_time_utc": spec["target_time_utc"],
                "last_input_close": last_input_close,
                "predicted_close": spec["predicted_close"],
                "actual_close": spec["actual_close"],
                "normalized_deviation_pct": spec["normalized_deviation_pct"],
                "signed_deviation_pct": spec["signed_deviation_pct"],
                "overshoot_label": spec["overshoot_label"],
            }
        )
    return rows


def create_sample_run(conn) -> tuple[int, int, int]:
    postgres_backtest = load_postgres_backtest_module()

    run_id = postgres_backtest.create_backtest_run(
        conn=conn,
        exchange="binance",
        symbol="BTCUSDT",
        interval="1m",
        model_repo_id="google/timesfm-1.0-200m",
        backend="cpu",
        freq_bucket=0,
        context_len=4,
        horizon_len=2,
        stride=1,
        batch_size=2,
        data_start_utc=utc("2024-04-01T00:00:00Z"),
        data_end_utc=utc("2024-04-01T00:05:00Z"),
        points=6,
        windows=2,
    )
    window_a_id = postgres_backtest.create_backtest_window(
        conn=conn,
        run_id=run_id,
        window_index=0,
        target_start_utc=utc("2024-04-01T00:04:00Z"),
        context_end_utc=utc("2024-04-01T00:03:00Z"),
        last_input_close=100.0,
    )
    window_b_id = postgres_backtest.create_backtest_window(
        conn=conn,
        run_id=run_id,
        window_index=1,
        target_start_utc=utc("2024-04-01T00:05:00Z"),
        context_end_utc=utc("2024-04-01T00:04:00Z"),
        last_input_close=100.0,
    )
    postgres_backtest.insert_backtest_steps(
        conn=conn,
        rows=[
            *build_step_rows(
                run_id,
                window_a_id,
                last_input_close=100.0,
                step_specs=[
                    {
                        "target_time_utc": utc("2024-04-01T00:04:00Z"),
                        "predicted_close": 103.0,
                        "actual_close": 102.0,
                        "normalized_deviation_pct": 1.0,
                        "signed_deviation_pct": 1.0,
                        "overshoot_label": "overshoot",
                    },
                    {
                        "target_time_utc": utc("2024-04-01T00:05:00Z"),
                        "predicted_close": 103.0,
                        "actual_close": 101.0,
                        "normalized_deviation_pct": 2.0,
                        "signed_deviation_pct": 2.0,
                        "overshoot_label": "overshoot",
                    },
                ],
            ),
            *build_step_rows(
                run_id,
                window_b_id,
                last_input_close=100.0,
                step_specs=[
                    {
                        "target_time_utc": utc("2024-04-01T00:05:00Z"),
                        "predicted_close": 98.0,
                        "actual_close": 101.0,
                        "normalized_deviation_pct": 3.0,
                        "signed_deviation_pct": -3.0,
                        "overshoot_label": "undershoot",
                    },
                    {
                        "target_time_utc": utc("2024-04-01T00:06:00Z"),
                        "predicted_close": 103.0,
                        "actual_close": 99.0,
                        "normalized_deviation_pct": 4.0,
                        "signed_deviation_pct": -4.0,
                        "overshoot_label": "undershoot",
                    },
                ],
            ),
        ],
    )
    return run_id, window_a_id, window_b_id


def test_bootstrap_schema_applies_all_checked_in_sql_files(postgres_test_database) -> None:
    with connect_postgres(settings=postgres_test_database, autocommit=False) as conn:
        bootstrap_schema(conn)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    to_regclass('market_data.assets')::text,
                    to_regclass('market_data.backtest_runs')::text,
                    to_regclass('market_data.backtest_windows')::text,
                    to_regclass('market_data.backtest_prediction_steps')::text,
                    to_regclass('market_data.backtest_step_stats_vw')::text
                """
            )
            result = cur.fetchone()

    assert result == (
        "market_data.assets",
        "market_data.backtest_runs",
        "market_data.backtest_windows",
        "market_data.backtest_prediction_steps",
        "market_data.backtest_step_stats_vw",
    )


def test_save_backtest_writes_run_window_and_step_rows(
    bootstrapped_postgres_connection,
) -> None:
    conn = bootstrapped_postgres_connection
    run_id, window_a_id, window_b_id = create_sample_run(conn)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT symbol, context_len, horizon_len, points, windows
            FROM market_data.backtest_runs
            WHERE run_id = %s
            """,
            (run_id,),
        )
        run_row = cur.fetchone()

        cur.execute(
            """
            SELECT window_index, target_start_utc, context_end_utc
            FROM market_data.backtest_windows
            WHERE run_id = %s
            ORDER BY window_index
            """,
            (run_id,),
        )
        window_rows = cur.fetchall()

        cur.execute(
            """
            SELECT window_id, step_index, predicted_close, actual_close, overshoot_label
            FROM market_data.backtest_prediction_steps
            WHERE run_id = %s
            ORDER BY window_id, step_index
            """,
            (run_id,),
        )
        step_rows = cur.fetchall()

    assert run_row == ("BTCUSDT", 4, 2, 6, 2)
    assert window_rows == [
        (0, utc("2024-04-01T00:04:00Z"), utc("2024-04-01T00:03:00Z")),
        (1, utc("2024-04-01T00:05:00Z"), utc("2024-04-01T00:04:00Z")),
    ]
    assert step_rows == [
        (window_a_id, 0, 103.0, 102.0, "overshoot"),
        (window_a_id, 1, 103.0, 101.0, "overshoot"),
        (window_b_id, 0, 98.0, 101.0, "undershoot"),
        (window_b_id, 1, 103.0, 99.0, "undershoot"),
    ]


def test_backtest_step_stats_view_exposes_grouped_stats_for_one_run(
    bootstrapped_postgres_connection,
) -> None:
    conn = bootstrapped_postgres_connection
    run_id, _, _ = create_sample_run(conn)
    postgres_backtest = load_postgres_backtest_module()

    stats_rows = postgres_backtest.query_backtest_step_stats(conn=conn, run_id=run_id)

    assert len(stats_rows) == 2

    step_zero = stats_rows[0]
    assert step_zero["run_id"] == run_id
    assert step_zero["step_index"] == 0
    assert step_zero["step_count"] == 2
    assert math.isclose(step_zero["avg_normalized_deviation_pct"], 2.0)
    assert math.isclose(step_zero["stddev_normalized_deviation_pct"], 1.0)
    assert step_zero["overshoot_count"] == 1
    assert step_zero["undershoot_count"] == 1
    assert math.isclose(step_zero["avg_signed_deviation_pct"], -1.0)

    step_one = stats_rows[1]
    assert step_one["run_id"] == run_id
    assert step_one["step_index"] == 1
    assert step_one["step_count"] == 2
    assert math.isclose(step_one["avg_normalized_deviation_pct"], 3.0)
    assert math.isclose(step_one["stddev_normalized_deviation_pct"], 1.0)
    assert step_one["overshoot_count"] == 1
    assert step_one["undershoot_count"] == 1
    assert math.isclose(step_one["avg_signed_deviation_pct"], -1.0)
