from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime

import psycopg


def create_backtest_run(
    conn: psycopg.Connection,
    *,
    exchange: str,
    symbol: str,
    interval: str,
    model_repo_id: str,
    backend: str,
    freq_bucket: int,
    context_len: int,
    horizon_len: int,
    stride: int,
    batch_size: int,
    data_start_utc: datetime,
    data_end_utc: datetime,
    points: int,
    windows: int,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO market_data.backtest_runs (
                exchange,
                symbol,
                interval,
                model_repo_id,
                backend,
                freq_bucket,
                context_len,
                horizon_len,
                stride,
                batch_size,
                data_start_utc,
                data_end_utc,
                points,
                windows
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING run_id
            """,
            (
                exchange,
                symbol,
                interval,
                model_repo_id,
                backend,
                freq_bucket,
                context_len,
                horizon_len,
                stride,
                batch_size,
                data_start_utc,
                data_end_utc,
                points,
                windows,
            ),
        )
        return int(cur.fetchone()[0])


def create_backtest_window(
    conn: psycopg.Connection,
    *,
    run_id: int,
    window_index: int,
    target_start_utc: datetime,
    context_end_utc: datetime,
    last_input_close: float,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO market_data.backtest_windows (
                run_id,
                window_index,
                target_start_utc,
                context_end_utc,
                last_input_close
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING window_id
            """,
            (
                run_id,
                window_index,
                target_start_utc,
                context_end_utc,
                last_input_close,
            ),
        )
        return int(cur.fetchone()[0])


def insert_backtest_steps(
    conn: psycopg.Connection,
    *,
    rows: Iterable[Mapping[str, object]],
) -> int:
    materialized_rows = list(rows)
    if not materialized_rows:
        return 0

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO market_data.backtest_prediction_steps (
                run_id,
                window_id,
                step_index,
                target_time_utc,
                last_input_close,
                predicted_close,
                actual_close,
                normalized_deviation_pct,
                signed_deviation_pct,
                overshoot_label
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    row["run_id"],
                    row["window_id"],
                    row["step_index"],
                    row["target_time_utc"],
                    row["last_input_close"],
                    row["predicted_close"],
                    row["actual_close"],
                    row["normalized_deviation_pct"],
                    row["signed_deviation_pct"],
                    row["overshoot_label"],
                )
                for row in materialized_rows
            ],
        )
    return len(materialized_rows)


def query_backtest_step_stats(
    conn: psycopg.Connection,
    *,
    run_id: int,
) -> list[dict[str, object]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                run_id,
                step_index,
                step_count,
                avg_normalized_deviation_pct,
                stddev_normalized_deviation_pct,
                overshoot_count,
                undershoot_count,
                match_count,
                avg_signed_deviation_pct
            FROM market_data.backtest_step_stats_vw
            WHERE run_id = %s
            ORDER BY step_index
            """,
            (run_id,),
        )
        rows = cur.fetchall()
        columns = [description.name for description in cur.description]

    return [dict(zip(columns, row)) for row in rows]
