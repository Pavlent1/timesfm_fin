from __future__ import annotations

import argparse
from datetime import datetime

import pandas as pd

from postgres_dataset import connect_postgres, load_postgres_settings
from postgres_discover_data import fetch_dataframe, parse_utc_datetime


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_postgres_settings()
    parser = argparse.ArgumentParser(
        description="Verify PostgreSQL dataset integrity for Phase 1."
    )
    parser.add_argument("--host", default=defaults.host, help="PostgreSQL host.")
    parser.add_argument("--port", type=int, default=defaults.port, help="PostgreSQL port.")
    parser.add_argument("--db-name", default=defaults.db_name, help="Database name.")
    parser.add_argument("--user", default=defaults.user, help="Database user.")
    parser.add_argument("--password", default=defaults.password, help="Database password.")
    parser.add_argument("--source", default=None, help="Filter by source name.")
    parser.add_argument("--symbol", default=None, help="Filter by symbol.")
    parser.add_argument("--timeframe", default=None, help="Filter by timeframe.")
    parser.add_argument("--start", type=parse_utc_datetime, default=None, help="UTC start filter.")
    parser.add_argument("--end", type=parse_utc_datetime, default=None, help="UTC end filter.")
    return parser.parse_args(argv)


def load_observations(
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
            s.series_id,
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
        ORDER BY s.series_id, o.observation_time_utc
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
        return frame

    frame["observation_time_utc"] = pd.to_datetime(frame["observation_time_utc"], utc=True)
    frame["close_price"] = frame["close_price"].astype(float)
    return frame


def build_integrity_report(
    conn,
    *,
    source: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict[str, object]:
    frame = load_observations(
        conn,
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
    )
    if frame.empty:
        return {
            "issue_counts": {
                "duplicate_timestamps": 0,
                "missing_minute_gaps": 0,
                "ordering_issues": 0,
                "null_values": 0,
                "out_of_range_timestamps": 0,
            },
            "coverage": pd.DataFrame(),
        }

    duplicate_timestamps = int(frame.duplicated(["series_id", "observation_time_utc"]).sum())
    null_values = int(frame["close_price"].isna().sum())
    out_of_range_timestamps = int(
        ((frame["observation_time_utc"].dt.second != 0) | (frame["observation_time_utc"].dt.microsecond != 0)).sum()
    )

    ordering_issues = 0
    missing_minute_gaps = 0
    coverage_rows: list[dict[str, object]] = []

    for (_, source_name, asset_symbol, series_timeframe), group in frame.groupby(
        ["series_id", "source_name", "symbol", "timeframe"],
        sort=True,
    ):
        timestamps = group["observation_time_utc"].reset_index(drop=True)
        diffs = timestamps.diff().dropna()
        ordering_issues += int((diffs <= pd.Timedelta(0)).sum())
        missing_minute_gaps += int(
            (((diffs[diffs > pd.Timedelta(minutes=1)] / pd.Timedelta(minutes=1)) - 1).sum())
        )
        coverage_rows.append(
            {
                "source_name": source_name,
                "symbol": asset_symbol,
                "timeframe": series_timeframe,
                "row_count": int(len(group)),
                "data_start_utc": timestamps.iloc[0],
                "data_end_utc": timestamps.iloc[-1],
            }
        )

    coverage = pd.DataFrame(coverage_rows).sort_values(
        ["source_name", "symbol", "timeframe"]
    ).reset_index(drop=True)

    return {
        "issue_counts": {
            "duplicate_timestamps": duplicate_timestamps,
            "missing_minute_gaps": missing_minute_gaps,
            "ordering_issues": ordering_issues,
            "null_values": null_values,
            "out_of_range_timestamps": out_of_range_timestamps,
        },
        "coverage": coverage,
    }


def render_integrity_report(report: dict[str, object]) -> str:
    issue_counts = report["issue_counts"]
    lines = ["Integrity summary:"]
    for key, value in issue_counts.items():
        lines.append(f"- {key}: {value}")

    coverage: pd.DataFrame = report["coverage"]
    if coverage.empty:
        lines.append("")
        lines.append("No matching PostgreSQL observations found.")
        return "\n".join(lines)

    display = coverage.copy()
    display["data_start_utc"] = display["data_start_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    display["data_end_utc"] = display["data_end_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    display = display.rename(columns={"source_name": "source", "row_count": "rows"})

    lines.append("")
    lines.append("Coverage summary:")
    lines.append(display.to_string(index=False))
    return "\n".join(lines)


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
        report = build_integrity_report(
            conn,
            source=args.source,
            symbol=args.symbol,
            timeframe=args.timeframe,
            start=args.start,
            end=args.end,
        )

    print(render_integrity_report(report))


if __name__ == "__main__":
    main()
