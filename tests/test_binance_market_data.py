from __future__ import annotations

import json
from email.message import Message
from urllib.error import HTTPError

import pytest

from binance_market_data import fetch_binance_klines


class JsonResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def scripted_reader(events: list[object], seen_urls: list[str]):
    def reader(request, timeout: int = 30):
        seen_urls.append(request.full_url)
        event = events.pop(0)
        if isinstance(event, Exception):
            raise event
        return JsonResponse(event)

    return reader


def rate_limit_error(retry_after: str) -> HTTPError:
    headers = Message()
    headers["Retry-After"] = retry_after
    return HTTPError(
        url="https://api.binance.com/api/v3/klines",
        code=429,
        msg="Too Many Requests",
        hdrs=headers,
        fp=None,
    )


def test_fetch_binance_klines_retries_after_http_429(monkeypatch) -> None:
    events = [
        rate_limit_error("0"),
        [
            [0, "first"],
            [60_000, "second"],
        ],
    ]
    seen_urls: list[str] = []
    sleeps: list[float] = []

    monkeypatch.setattr("binance_market_data.time.sleep", sleeps.append)

    rows = fetch_binance_klines(
        symbol="BTCUSDT",
        start_ms=0,
        end_ms=120_000,
        reader=scripted_reader(events, seen_urls),
    )

    assert [row[0] for row in rows] == [0, 60_000]
    assert sleeps == [0.0]
    assert len(seen_urls) == 2
    assert "symbol=BTCUSDT" in seen_urls[0]
    assert "startTime=0" in seen_urls[0]


def test_fetch_binance_klines_rejects_malformed_payload() -> None:
    with pytest.raises(ValueError, match="Unexpected Binance response"):
        fetch_binance_klines(
            symbol="BTCUSDT",
            start_ms=0,
            end_ms=60_000,
            reader=scripted_reader([{"not": "a list"}], []),
        )


def test_fetch_binance_klines_deduplicates_duplicate_timestamps() -> None:
    rows = fetch_binance_klines(
        symbol="BTCUSDT",
        start_ms=0,
        end_ms=180_000,
        reader=scripted_reader(
            [
                [
                    [0, "first-page-open"],
                    [60_000, "first-page-close"],
                ],
                [
                    [60_000, "second-page-replacement"],
                    [120_000, "third-minute"],
                ],
            ],
            [],
        ),
    )

    assert [row[0] for row in rows] == [0, 60_000, 120_000]
    assert rows[1][1] == "second-page-replacement"


def test_fetch_binance_klines_raises_when_pagination_stalls() -> None:
    with pytest.raises(RuntimeError, match="pagination stalled"):
        fetch_binance_klines(
            symbol="BTCUSDT",
            start_ms=60_000,
            end_ms=120_000,
            reader=scripted_reader(
                [
                    [
                        [0, "stale-row"],
                    ]
                ],
                [],
            ),
        )
