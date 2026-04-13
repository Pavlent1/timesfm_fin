from __future__ import annotations

import argparse
from pathlib import Path

from postgres_dataset import (
    PostgresSettings,
    bootstrap_schema,
    connect_postgres,
    default_schema_path,
    load_postgres_settings,
    wait_for_postgres,
)


def parse_args() -> argparse.Namespace:
    defaults = load_postgres_settings()

    parser = argparse.ArgumentParser(
        description="Apply the checked-in PostgreSQL Phase 1 schema."
    )
    parser.add_argument("--host", default=defaults.host, help="PostgreSQL host.")
    parser.add_argument("--port", type=int, default=defaults.port, help="PostgreSQL port.")
    parser.add_argument("--db-name", default=defaults.db_name, help="Database name.")
    parser.add_argument("--user", default=defaults.user, help="Database user.")
    parser.add_argument(
        "--password",
        default=defaults.password,
        help="Database password.",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=default_schema_path(),
        help="SQL file applied to the target database.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=float,
        default=60.0,
        help="How long to wait for PostgreSQL before applying the schema.",
    )
    parser.add_argument(
        "--skip-wait",
        action="store_true",
        help="Do not wait for PostgreSQL readiness before applying the schema.",
    )
    return parser.parse_args()


def build_settings(args: argparse.Namespace) -> PostgresSettings:
    return PostgresSettings(
        host=args.host,
        port=args.port,
        db_name=args.db_name,
        user=args.user,
        password=args.password,
    )


def main() -> None:
    args = parse_args()
    settings = build_settings(args)

    if not args.skip_wait:
        wait_for_postgres(settings=settings, timeout_seconds=args.wait_seconds)

    with connect_postgres(settings=settings, autocommit=False) as conn:
        bootstrap_schema(conn=conn, schema_path=args.schema_file)

    print(
        f"Applied schema {args.schema_file} to "
        f"{settings.host}:{settings.port}/{settings.db_name}."
    )


if __name__ == "__main__":
    main()
