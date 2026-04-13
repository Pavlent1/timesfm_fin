from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Callable

from binance_market_data import BINANCE_KLINES_URL, fetch_binance_klines
from postgres_dataset import (
    connect_postgres,
    ensure_series,
    finalize_ingestion_run,
    load_postgres_settings,
    mark_ingestion_failed,
    start_ingestion_run,
    upsert_observations,
)


def parse_utc_datetime(value: str) -> datetime:
    if len(value) == 10:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def default_end_utc(now: datetime | None = None) -> datetime:
    reference = now or datetime.now(timezone.utc)
    return reference.replace(second=0, microsecond=0)


def default_start_utc(end_utc: datetime, days: int) -> datetime:
    return end_utc - timedelta(days=days)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_postgres_settings()

    parser = argparse.ArgumentParser(
        description="Ingest Binance close-price candles into PostgreSQL."
    )
    parser.add_argument("--host", default=defaults.host, help="PostgreSQL host.")
    parser.add_argument("--port", type=int, default=defaults.port, help="PostgreSQL port.")
    parser.add_argument("--db-name", default=defaults.db_name, help="Database name.")
    parser.add_argument("--user", default=defaults.user, help="Database user.")
    parser.add_argument("--password", default=defaults.password, help="Database password.")
    parser.add_argument("--source-name", default="binance", help="Logical data source name.")
    parser.add_argument("--symbol", default="BTCUSDT", help="Binance spot symbol.")
    parser.add_argument("--timeframe", default="1m", help="Binance interval.")
    parser.add_argument("--days", type=int, default=365, help="Default lookback window in days.")
    parser.add_argument(
        "--start",
        type=parse_utc_datetime,
        default=None,
        help="UTC start as YYYY-MM-DD or ISO timestamp.",
    )
    parser.add_argument(
        "--end",
        type=parse_utc_datetime,
        default=None,
        help="UTC end as YYYY-MM-DD or ISO timestamp.",
    )
    return parser.parse_args(argv)


def normalize_close_observations(rows: list[list]) -> list[tuple[datetime, float]]:
    return [
        (
            datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc),
            float(row[4]),
        )
        for row in rows
    ]


def persist_ingestion_rows(
    conn,
    *,
    ingestion_run_id: int,
    series_id: int,
    requested_start_utc: datetime,
    requested_end_utc: datetime,
    rows: list[list],
) -> dict[str, object]:
    observations = normalize_close_observations(rows)
    actual_start_utc = observations[0][0] if observations else None
    actual_end_utc = observations[-1][0] if observations else None
    rows_written = upsert_observations(
        conn=conn,
        series_id=series_id,
        ingestion_run_id=ingestion_run_id,
        observations=observations,
    )
    status = "completed" if rows else "empty"
    finalize_ingestion_run(
        conn=conn,
        ingestion_run_id=ingestion_run_id,
        actual_start_utc=actual_start_utc,
        actual_end_utc=actual_end_utc,
        rows_written=rows_written,
        status=status,
    )
    conn.commit()

    return {
        "series_id": series_id,
        "ingestion_run_id": ingestion_run_id,
        "requested_start_utc": requested_start_utc,
        "requested_end_utc": requested_end_utc,
        "actual_start_utc": actual_start_utc,
        "actual_end_utc": actual_end_utc,
        "rows_written": rows_written,
        "status": status,
    }


def ingest_binance_rows(
    conn,
    *,
    symbol: str,
    source_name: str,
    timeframe: str,
    requested_start_utc: datetime,
    requested_end_utc: datetime,
    rows: list[list],
    source_endpoint: str = BINANCE_KLINES_URL,
) -> dict[str, object]:
    series_id = ensure_series(
        conn=conn,
        symbol=symbol,
        source_name=source_name,
        timeframe=timeframe,
    )
    ingestion_run_id = start_ingestion_run(
        conn=conn,
        series_id=series_id,
        source_endpoint=source_endpoint,
        requested_start_utc=requested_start_utc,
        requested_end_utc=requested_end_utc,
        notes={"symbol": symbol, "timeframe": timeframe},
    )
    return persist_ingestion_rows(
        conn,
        ingestion_run_id=ingestion_run_id,
        series_id=series_id,
        requested_start_utc=requested_start_utc,
        requested_end_utc=requested_end_utc,
        rows=rows,
    )


def run_ingest(
    args: argparse.Namespace,
    *,
    fetcher: Callable[..., list[list]] = fetch_binance_klines,
    now: datetime | None = None,
) -> dict[str, object]:
    end_utc = args.end or default_end_utc(now=now)
    start_utc = args.start or default_start_utc(end_utc=end_utc, days=args.days)
    settings = load_postgres_settings(
        {
            "POSTGRES_HOST": args.host,
            "POSTGRES_PORT": str(args.port),
            "POSTGRES_DB": args.db_name,
            "POSTGRES_USER": args.user,
            "POSTGRES_PASSWORD": args.password,
        }
    )

    with connect_postgres(settings=settings, autocommit=False) as conn:
        series_id = ensure_series(
            conn=conn,
            symbol=args.symbol,
            source_name=args.source_name,
            timeframe=args.timeframe,
        )
        ingestion_run_id = start_ingestion_run(
            conn=conn,
            series_id=series_id,
            source_endpoint=BINANCE_KLINES_URL,
            requested_start_utc=start_utc,
            requested_end_utc=end_utc,
            notes={"symbol": args.symbol, "timeframe": args.timeframe},
        )
        conn.commit()

        try:
            rows = fetcher(
                symbol=args.symbol,
                start_ms=int(start_utc.timestamp() * 1000),
                end_ms=int(end_utc.timestamp() * 1000),
                interval=args.timeframe,
            )
            result = persist_ingestion_rows(
                conn,
                ingestion_run_id=ingestion_run_id,
                series_id=series_id,
                requested_start_utc=start_utc,
                requested_end_utc=end_utc,
                rows=rows,
            )
        except Exception as exc:
            mark_ingestion_failed(
                conn,
                ingestion_run_id=ingestion_run_id,
                error_message=str(exc),
            )
            conn.commit()
            raise

    return result


def print_summary(result: dict[str, object], symbol: str, timeframe: str) -> None:
    print(f"Source: Binance")
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Status: {result['status']}")
    print(f"Ingestion run id: {result['ingestion_run_id']}")
    print(f"Rows written: {result['rows_written']}")
    print(f"Requested range: {result['requested_start_utc']} -> {result['requested_end_utc']}")
    print(f"Actual range: {result['actual_start_utc']} -> {result['actual_end_utc']}")


def main() -> None:
    args = parse_args()
    result = run_ingest(args)
    print_summary(result=result, symbol=args.symbol, timeframe=args.timeframe)


if __name__ == "__main__":
    main()
