from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

import pandas as pd

from postgres_dataset import connect_postgres, load_postgres_settings
from postgres_ingest_binance import (
    build_ingest_args,
    default_end_utc,
    parse_utc_datetime,
    run_ingest,
)
from postgres_verify_data import build_integrity_report, load_observations


SUPPORTED_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
DEFAULT_TARGET_MONTHS = {
    "BTCUSDT": 40,
    "ETHUSDT": 36,
    "SOLUSDT": 36,
}
DEFAULT_RESERVE_MONTHS = {
    "BTCUSDT": 4,
    "ETHUSDT": 0,
    "SOLUSDT": 0,
}
DEFAULT_REPAIRABLE_GAP_MINUTES = 5
APPROXIMATE_DAYS_PER_MONTH = 30


def month_lookback_start(end_utc: datetime, months: int) -> datetime:
    if months < 0:
        raise ValueError("Target months must be non-negative.")
    return end_utc - timedelta(days=months * APPROXIMATE_DAYS_PER_MONTH)


def normalize_symbols(symbols: list[str] | None = None) -> list[str]:
    selected = symbols or list(SUPPORTED_SYMBOLS)
    normalized: list[str] = []
    for symbol in selected:
        if symbol not in SUPPORTED_SYMBOLS:
            raise ValueError(
                "Unsupported symbol "
                f"{symbol}. Phase 3 source preparation only supports "
                + ", ".join(SUPPORTED_SYMBOLS)
                + "."
            )
        if symbol not in normalized:
            normalized.append(symbol)
    return normalized


def resolve_source_targets(
    symbols: list[str] | None = None,
    *,
    target_months_by_symbol: dict[str, int] | None = None,
) -> dict[str, int]:
    selected = normalize_symbols(symbols)
    if target_months_by_symbol is None:
        target_months_by_symbol = DEFAULT_TARGET_MONTHS

    resolved: dict[str, int] = {}
    for symbol in selected:
        if symbol not in target_months_by_symbol:
            raise ValueError(f"Missing target month definition for {symbol}.")
        resolved[symbol] = int(target_months_by_symbol[symbol])
    return resolved


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_postgres_settings()
    parser = argparse.ArgumentParser(
        description="Backfill and verify the Phase 3 PostgreSQL training source."
    )
    parser.add_argument("--host", default=getattr(defaults, "host", None), help="PostgreSQL host.")
    parser.add_argument(
        "--port",
        type=int,
        default=getattr(defaults, "port", None),
        help="PostgreSQL port.",
    )
    parser.add_argument(
        "--db-name",
        default=getattr(defaults, "db_name", None),
        help="Database name.",
    )
    parser.add_argument("--user", default=getattr(defaults, "user", None), help="Database user.")
    parser.add_argument(
        "--password",
        default=getattr(defaults, "password", None),
        help="Database password.",
    )
    parser.add_argument("--source-name", default="binance", help="Logical data source name.")
    parser.add_argument("--timeframe", default="1m", help="Binance interval.")
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=list(SUPPORTED_SYMBOLS),
        help="Phase 3 symbols to backfill and verify.",
    )
    parser.add_argument(
        "--end",
        type=parse_utc_datetime,
        default=None,
        help="UTC end as YYYY-MM-DD or ISO timestamp.",
    )
    parser.add_argument(
        "--skip-backfill",
        action="store_true",
        help="Only run readiness checks against PostgreSQL.",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_false",
        dest="strict",
        help="Report blocking findings without raising a non-zero failure.",
    )
    parser.set_defaults(strict=True)
    return parser.parse_args(argv)


def _build_series_details_from_frame(
    frame: pd.DataFrame,
    *,
    repairable_gap_minutes: int = DEFAULT_REPAIRABLE_GAP_MINUTES,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if frame.empty:
        return [], []

    series_details: list[dict[str, object]] = []
    blocking_findings: list[dict[str, object]] = []

    for (_, source_name, symbol, timeframe), group in frame.groupby(
        ["series_id", "source_name", "symbol", "timeframe"],
        sort=True,
    ):
        timestamps = group["observation_time_utc"].reset_index(drop=True)
        segments: list[dict[str, object]] = []
        gaps: list[dict[str, object]] = []

        segment_start_index = 0
        for index in range(1, len(timestamps)):
            delta = timestamps.iloc[index] - timestamps.iloc[index - 1]
            if delta <= pd.Timedelta(minutes=1):
                continue

            segment = timestamps.iloc[segment_start_index:index]
            segments.append(
                {
                    "start_utc": segment.iloc[0],
                    "end_utc": segment.iloc[-1],
                    "row_count": int(len(segment)),
                }
            )
            missing_minutes = int(delta / pd.Timedelta(minutes=1)) - 1
            severity = (
                "repairable"
                if missing_minutes <= repairable_gap_minutes
                else "blocking"
            )
            gap = {
                "start_utc": timestamps.iloc[index - 1],
                "end_utc": timestamps.iloc[index],
                "missing_minutes": missing_minutes,
                "severity": severity,
            }
            gaps.append(gap)
            if severity == "blocking":
                blocking_findings.append(
                    {
                        "symbol": symbol,
                        "kind": "blocking_gap",
                        "message": (
                            f"{symbol} has a blocking gap of {missing_minutes} missing "
                            "minute candles."
                        ),
                        "gap": gap,
                    }
                )
            segment_start_index = index

        final_segment = timestamps.iloc[segment_start_index:]
        segments.append(
            {
                "start_utc": final_segment.iloc[0],
                "end_utc": final_segment.iloc[-1],
                "row_count": int(len(final_segment)),
            }
        )

        detail = {
            "source_name": source_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "data_start_utc": timestamps.iloc[0],
            "data_end_utc": timestamps.iloc[-1],
            "coverage_state": "contiguous" if not gaps else "segmented",
            "segment_count": len(segments),
            "segments": segments,
            "gaps": gaps,
            "blocking_gap_count": sum(1 for gap in gaps if gap["severity"] == "blocking"),
            "repairable_gap_count": sum(
                1 for gap in gaps if gap["severity"] == "repairable"
            ),
        }
        series_details.append(detail)

    return series_details, blocking_findings


def load_source_integrity_report(
    conn,
    *,
    source_name: str,
    timeframe: str,
    repairable_gap_minutes: int = DEFAULT_REPAIRABLE_GAP_MINUTES,
) -> dict[str, object]:
    report = build_integrity_report(
        conn,
        source=source_name,
        timeframe=timeframe,
    )
    if "series_details" in report and "blocking_findings" in report:
        return report

    frame = load_observations(
        conn,
        source=source_name,
        timeframe=timeframe,
    )
    series_details, blocking_findings = _build_series_details_from_frame(
        frame,
        repairable_gap_minutes=repairable_gap_minutes,
    )
    report["series_details"] = series_details
    report["blocking_findings"] = blocking_findings
    return report


def evaluate_symbol_readiness(
    detail: dict[str, object] | None,
    *,
    target_months: int,
    end_utc: datetime,
    reserve_months: int = 0,
) -> dict[str, object]:
    if detail is None:
        return {
            "coverage_met": False,
            "reserve_months": reserve_months,
            "reserve_ready": False,
            "blocking_reasons": ["No PostgreSQL coverage found for this symbol."],
        }

    target_start_utc = month_lookback_start(end_utc, target_months)
    data_start_utc: datetime = detail["data_start_utc"]
    data_end_utc: datetime = detail["data_end_utc"]

    coverage_met = data_start_utc <= target_start_utc
    reserve_ready = reserve_months == 0 or (
        coverage_met and data_end_utc >= month_lookback_start(end_utc, reserve_months)
    )

    blocking_reasons: list[str] = []
    if not coverage_met:
        blocking_reasons.append(
            "Historical coverage does not reach the required target window."
        )
    if detail["blocking_gap_count"] > 0:
        blocking_reasons.append(
            f"{detail['blocking_gap_count']} blocking gap(s) remain in the selected history."
        )
    if reserve_months > 0 and not reserve_ready:
        blocking_reasons.append(
            f"The latest {reserve_months} BTC month(s) cannot remain reserved for backtests."
        )

    readiness = dict(detail)
    readiness.update(
        {
            "target_months": target_months,
            "target_start_utc": target_start_utc,
            "coverage_met": coverage_met,
            "reserve_months": reserve_months,
            "reserve_ready": reserve_ready,
            "blocking_reasons": blocking_reasons,
        }
    )
    return readiness


def build_source_readiness_report(
    conn,
    *,
    symbols: list[str] | None = None,
    source_name: str = "binance",
    timeframe: str = "1m",
    end_utc: datetime | None = None,
    target_months_by_symbol: dict[str, int] | None = None,
    reserve_months_by_symbol: dict[str, int] | None = None,
    repairable_gap_minutes: int = DEFAULT_REPAIRABLE_GAP_MINUTES,
) -> dict[str, object]:
    selected = normalize_symbols(symbols)
    targets = resolve_source_targets(
        selected,
        target_months_by_symbol=target_months_by_symbol,
    )
    reserves = {
        symbol: int((reserve_months_by_symbol or DEFAULT_RESERVE_MONTHS).get(symbol, 0))
        for symbol in selected
    }
    resolved_end_utc = end_utc or default_end_utc()

    integrity = load_source_integrity_report(
        conn,
        source_name=source_name,
        timeframe=timeframe,
        repairable_gap_minutes=repairable_gap_minutes,
    )
    details_by_symbol = {
        detail["symbol"]: detail
        for detail in integrity["series_details"]
    }

    symbol_reports: dict[str, dict[str, object]] = {}
    blocking_findings: list[dict[str, object]] = []
    for symbol in selected:
        detail = details_by_symbol.get(symbol)
        readiness = evaluate_symbol_readiness(
            detail,
            target_months=targets[symbol],
            end_utc=resolved_end_utc,
            reserve_months=reserves[symbol],
        )
        symbol_reports[symbol] = readiness

        if detail is None:
            blocking_findings.append(
                {
                    "symbol": symbol,
                    "kind": "missing_symbol",
                    "message": f"{symbol} is missing from PostgreSQL.",
                }
            )
            continue

        if not readiness["coverage_met"]:
            blocking_findings.append(
                {
                    "symbol": symbol,
                    "kind": "insufficient_coverage",
                    "message": (
                        f"{symbol} does not meet the {targets[symbol]} month coverage target."
                    ),
                }
            )
        if readiness["blocking_gap_count"] > 0:
            blocking_findings.extend(
                finding
                for finding in integrity["blocking_findings"]
                if finding["symbol"] == symbol
            )
        if reserves[symbol] > 0 and not readiness["reserve_ready"]:
            blocking_findings.append(
                {
                    "symbol": symbol,
                    "kind": "reserve_unavailable",
                    "message": (
                        f"{symbol} cannot preserve the latest {reserves[symbol]} "
                        "months for backtests."
                    ),
                }
            )

    return {
        "ready": not blocking_findings,
        "requested_end_utc": resolved_end_utc,
        "symbols": symbol_reports,
        "blocking_findings": blocking_findings,
        "integrity_report": integrity,
    }


def assert_training_source_ready(report: dict[str, object]) -> None:
    findings = report.get("blocking_findings", [])
    if not findings:
        return

    messages = [
        f"{finding['symbol']}: {finding['message']}"
        for finding in findings
    ]
    raise ValueError("Phase 3 source readiness failed: " + " ".join(messages))


def render_source_readiness(report: dict[str, object]) -> str:
    lines = [
        "Phase 3 source readiness:",
        f"Ready: {'yes' if report['ready'] else 'no'}",
        "",
    ]
    for symbol, readiness in report["symbols"].items():
        coverage_state = readiness.get("coverage_state", "missing")
        lines.append(
            f"{symbol}: state={coverage_state}, "
            f"coverage_met={readiness['coverage_met']}, "
            f"reserve_ready={readiness['reserve_ready']}"
        )
        for reason in readiness["blocking_reasons"]:
            lines.append(f"  - {reason}")
    if report["blocking_findings"]:
        lines.append("")
        lines.append("Blocking findings:")
        for finding in report["blocking_findings"]:
            lines.append(f"- {finding['symbol']}: {finding['message']}")
    return "\n".join(lines)


def run_source_preparation(
    args: argparse.Namespace,
    *,
    ingest_runner=run_ingest,
    now: datetime | None = None,
) -> dict[str, object]:
    selected = normalize_symbols(args.symbols)
    end_utc = args.end or default_end_utc(now=now)
    targets = resolve_source_targets(selected)

    if not args.skip_backfill:
        for symbol in selected:
            start_utc = month_lookback_start(end_utc, targets[symbol])
            ingest_args = build_ingest_args(
                args,
                symbol=symbol,
                start=start_utc,
                end=end_utc,
            )
            ingest_runner(ingest_args, now=end_utc)

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
        report = build_source_readiness_report(
            conn,
            symbols=selected,
            source_name=args.source_name,
            timeframe=args.timeframe,
            end_utc=end_utc,
            target_months_by_symbol=targets,
        )

    if args.strict:
        assert_training_source_ready(report)
    return report


def main() -> None:
    args = parse_args()
    report = run_source_preparation(args)
    print(render_source_readiness(report))


if __name__ == "__main__":
    main()
