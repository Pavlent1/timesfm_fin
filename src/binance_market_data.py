from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
ONE_MINUTE_MS = 60_000


def to_utc_iso(timestamp_ms: int) -> str:
    return (
        datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def fetch_binance_klines(
    symbol: str,
    start_ms: int,
    end_ms: int,
    interval: str = "1m",
    limit: int = 1000,
    user_agent: str = "timesfm-fin/binance-market-data",
    reader: Callable = urlopen,
) -> list[list]:
    all_rows: list[list] = []
    cursor = start_ms

    while cursor < end_ms:
        params = urlencode(
            {
                "symbol": symbol,
                "interval": interval,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": limit,
            }
        )
        request = Request(
            f"{BINANCE_KLINES_URL}?{params}",
            headers={"User-Agent": user_agent},
        )

        try:
            with reader(request, timeout=30) as response:
                batch = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            retry_after = exc.headers.get("Retry-After")
            if exc.code == 429 and retry_after is not None:
                time.sleep(float(retry_after))
                continue
            raise

        if not isinstance(batch, list):
            raise ValueError(f"Unexpected Binance response: {batch!r}")
        if not batch:
            break

        all_rows.extend(batch)
        next_cursor = int(batch[-1][0]) + ONE_MINUTE_MS
        if next_cursor <= cursor:
            raise RuntimeError("Binance pagination stalled while fetching klines.")
        cursor = next_cursor

    unique_rows = {int(row[0]): row for row in all_rows}
    return [
        unique_rows[open_time]
        for open_time in sorted(unique_rows)
        if start_ms <= open_time < end_ms
    ]
