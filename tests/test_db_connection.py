from __future__ import annotations

from postgres_dataset import (
    DEFAULT_POSTGRES_DB,
    DEFAULT_POSTGRES_HOST,
    DEFAULT_POSTGRES_PASSWORD,
    DEFAULT_POSTGRES_PORT,
    DEFAULT_POSTGRES_USER,
    connect_postgres,
    load_postgres_settings,
)


def test_load_postgres_settings_uses_repo_defaults() -> None:
    settings = load_postgres_settings(env={})

    assert settings.host == DEFAULT_POSTGRES_HOST
    assert settings.port == DEFAULT_POSTGRES_PORT
    assert settings.db_name == DEFAULT_POSTGRES_DB
    assert settings.user == DEFAULT_POSTGRES_USER
    assert settings.password == DEFAULT_POSTGRES_PASSWORD


def test_project_code_connects_to_compose_managed_postgres(postgres_test_database) -> None:
    with connect_postgres(settings=postgres_test_database, autocommit=True) as conn:
        assert conn.execute("SELECT current_database()").fetchone()[0] == postgres_test_database.db_name
