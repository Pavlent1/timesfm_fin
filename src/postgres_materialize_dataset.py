from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from postgres_dataset import connect_postgres, load_postgres_settings
from postgres_discover_data import fetch_dataframe, parse_utc_datetime


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_postgres_settings()
    parser = argparse.ArgumentParser(
        description="Export PostgreSQL market data into CSV formats used by the repo."
    )
    parser.add_argument("--host", default=defaults.host, help="PostgreSQL host.")
    parser.add_argument("--port", type=int, default=defaults.port, help="PostgreSQL port.")
    parser.add_argument("--db-name", default=defaults.db_name, help="Database name.")
    parser.add_argument("--user", default=defaults.user, help="Database user.")
    parser.add_argument("--password", default=defaults.password, help="Database password.")
    parser.add_argument("--source", default=None, help="Filter by source name.")
    parser.add_argument("--symbol", default=None, help="Filter by symbol.")
    parser.add_argument("--timeframe", default="1m", help="Filter by timeframe.")
    parser.add_argument("--start", type=parse_utc_datetime, default=None, help="UTC start filter.")
    parser.add_argument("--end", type=parse_utc_datetime, default=None, help="UTC end filter.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["series_csv", "training_matrix"],
        help="Export layout for forecasting/evaluation or training.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        required=True,
        help="Output CSV file path.",
    )
    return parser.parse_args(argv)


def load_matching_observations(
    conn,
    *,
    source: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    frame = fetch_dataframe(
        conn,
        """
        SELECT
            s.source_name,
            a.symbol,
            s.timeframe,
            o.observation_time_utc,
            o.close_price
        FROM market_data.series AS s
        JOIN market_data.assets AS a ON a.asset_id = s.asset_id
        JOIN market_data.observations AS o ON o.series_id = s.series_id
        WHERE (%s::text IS NULL OR s.source_name = %s::text)
          AND (%s::text IS NULL OR a.symbol = %s::text)
          AND (%s::text IS NULL OR s.timeframe = %s::text)
          AND (%s::timestamptz IS NULL OR o.observation_time_utc >= %s::timestamptz)
          AND (%s::timestamptz IS NULL OR o.observation_time_utc < %s::timestamptz)
        ORDER BY s.source_name, a.symbol, s.timeframe, o.observation_time_utc
        """,
        (
            source,
            source,
            symbol,
            symbol,
            timeframe,
            timeframe,
            start,
            start,
            end,
            end,
        ),
    )
    if frame.empty:
        raise ValueError("No matching PostgreSQL observations found for materialization.")

    frame["observation_time_utc"] = pd.to_datetime(frame["observation_time_utc"], utc=True)
    frame["close_price"] = frame["close_price"].astype(float)
    frame["series_label"] = frame.apply(
        lambda row: f"{row['source_name']}__{row['symbol']}__{row['timeframe']}",
        axis=1,
    )
    return frame


def materialize_series_csv(frame: pd.DataFrame) -> pd.DataFrame:
    series_labels = frame["series_label"].drop_duplicates().tolist()
    if len(series_labels) != 1:
        raise ValueError(
            "series_csv mode requires exactly one matching series. "
            f"Matched {len(series_labels)} series: {series_labels}"
        )

    output = frame[["observation_time_utc", "close_price"]].copy()
    output = output.sort_values("observation_time_utc").reset_index(drop=True)
    output["Date"] = output["observation_time_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    output["Close"] = output["close_price"].astype(float)
    return output[["Date", "Close"]]


def materialize_training_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    pivot = frame.pivot(
        index="observation_time_utc",
        columns="series_label",
        values="close_price",
    ).sort_index()
    pivot = pivot.dropna(axis=0, how="any")
    if pivot.empty:
        raise ValueError(
            "training_matrix mode produced no fully aligned timestamps after filtering."
        )
    return pivot.reset_index(drop=True)


def write_materialized_csv(frame: pd.DataFrame, output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_csv, index=False)


def render_summary(mode: str, output_csv: Path, frame: pd.DataFrame) -> str:
    return (
        f"Mode: {mode}\n"
        f"Rows: {len(frame)}\n"
        f"Columns: {len(frame.columns)}\n"
        f"Saved to: {output_csv}"
    )


def main() -> None:
    args = parse_args()
    settings = load_postgres_settings(
        {
            "POSTGRES_HOST": args.host,
            "POSTGRES_PORT": str(args.port),
            "POSTGRES_DB": args.db_name,
            "POSTGRES_USER": args.user,
            "POSTGRES_PASSWORD": args.password,
        }
    )

    with connect_postgres(settings=settings, autocommit=True) as conn:
        frame = load_matching_observations(
            conn,
            source=args.source,
            symbol=args.symbol,
            timeframe=args.timeframe,
            start=args.start,
            end=args.end,
        )

    output = (
        materialize_series_csv(frame)
        if args.mode == "series_csv"
        else materialize_training_matrix(frame)
    )
    write_materialized_csv(output, args.output_csv)
    print(render_summary(args.mode, args.output_csv, output))


if __name__ == "__main__":
    main()
