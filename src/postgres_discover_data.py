from __future__ import annotations

import argparse
from datetime import datetime, timezone

import pandas as pd

from postgres_dataset import connect_postgres, load_postgres_settings


SORT_COLUMNS = {
    "source": "source_name",
    "symbol": "symbol",
    "timeframe": "timeframe",
    "rows": "row_count",
    "start": "data_start_utc",
    "end": "data_end_utc",
}


def parse_utc_datetime(value: str) -> datetime:
    if len(value) == 10:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_postgres_settings()
    parser = argparse.ArgumentParser(
        description="Inspect which datasets exist in PostgreSQL."
    )
    parser.add_argument("--host", default=defaults.host, help="PostgreSQL host.")
    parser.add_argument("--port", type=int, default=defaults.port, help="PostgreSQL port.")
    parser.add_argument("--db-name", default=defaults.db_name, help="Database name.")
    parser.add_argument("--user", default=defaults.user, help="Database user.")
    parser.add_argument("--password", default=defaults.password, help="Database password.")
    parser.add_argument("--source", default=None, help="Filter by source name.")
    parser.add_argument("--symbol", default=None, help="Filter by asset symbol.")
    parser.add_argument("--timeframe", default=None, help="Filter by timeframe.")
    parser.add_argument("--start", type=parse_utc_datetime, default=None, help="UTC start filter.")
    parser.add_argument("--end", type=parse_utc_datetime, default=None, help="UTC end filter.")
    parser.add_argument(
        "--sort-by",
        default="symbol",
        choices=sorted(SORT_COLUMNS),
        help="Allowed sort key for deterministic output.",
    )
    parser.add_argument(
        "--descending",
        action="store_true",
        help="Reverse the primary sort key.",
    )
    return parser.parse_args(argv)


def fetch_dataframe(conn, query: str, params: tuple) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        columns = [column.name for column in cur.description]
    return pd.DataFrame(rows, columns=columns)


def discover_series(
    conn,
    *,
    source: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    sort_by: str = "symbol",
    descending: bool = False,
) -> pd.DataFrame:
    order_column = SORT_COLUMNS[sort_by]
    direction = "DESC" if descending else "ASC"
    query = f"""
    SELECT
        s.source_name,
        a.symbol,
        s.timeframe,
        COUNT(o.observation_time_utc) AS row_count,
        MIN(o.observation_time_utc) AS data_start_utc,
        MAX(o.observation_time_utc) AS data_end_utc,
        MAX(ir.completed_at_utc) AS last_completed_at_utc
    FROM market_data.series AS s
    JOIN market_data.assets AS a ON a.asset_id = s.asset_id
    LEFT JOIN market_data.observations AS o ON o.series_id = s.series_id
    LEFT JOIN market_data.ingestion_runs AS ir ON ir.series_id = s.series_id
    WHERE (%s::text IS NULL OR s.source_name = %s::text)
      AND (%s::text IS NULL OR a.symbol = %s::text)
      AND (%s::text IS NULL OR s.timeframe = %s::text)
      AND (%s::timestamptz IS NULL OR o.observation_time_utc >= %s::timestamptz)
      AND (%s::timestamptz IS NULL OR o.observation_time_utc < %s::timestamptz)
    GROUP BY s.series_id, s.source_name, a.symbol, s.timeframe
    HAVING COUNT(o.observation_time_utc) > 0
    ORDER BY {order_column} {direction}, s.source_name ASC, a.symbol ASC, s.timeframe ASC
    """
    frame = fetch_dataframe(
        conn,
        query,
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

    for column in ["data_start_utc", "data_end_utc", "last_completed_at_utc"]:
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame["row_count"] = frame["row_count"].astype(int)
    return frame.reset_index(drop=True)


def render_discovery_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "No matching PostgreSQL datasets found."

    display = frame.copy()
    for column in ["data_start_utc", "data_end_utc", "last_completed_at_utc"]:
        display[column] = display[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    display = display.rename(
        columns={
            "source_name": "source",
            "row_count": "rows",
        }
    )
    return display.to_string(index=False)


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
        frame = discover_series(
            conn,
            source=args.source,
            symbol=args.symbol,
            timeframe=args.timeframe,
            start=args.start,
            end=args.end,
            sort_by=args.sort_by,
            descending=args.descending,
        )

    print(render_discovery_table(frame))


if __name__ == "__main__":
    main()
