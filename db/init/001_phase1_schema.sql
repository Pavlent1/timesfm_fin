CREATE SCHEMA IF NOT EXISTS market_data;

CREATE TABLE IF NOT EXISTS market_data.assets (
    asset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    asset_type TEXT NOT NULL DEFAULT 'spot',
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_data.series (
    series_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id BIGINT NOT NULL REFERENCES market_data.assets (asset_id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    field_name TEXT NOT NULL DEFAULT 'close_price',
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (asset_id, source_name, timeframe, field_name)
);

CREATE TABLE IF NOT EXISTS market_data.ingestion_runs (
    ingestion_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    series_id BIGINT NOT NULL REFERENCES market_data.series (series_id) ON DELETE CASCADE,
    source_endpoint TEXT NOT NULL,
    requested_start_utc TIMESTAMPTZ NOT NULL,
    requested_end_utc TIMESTAMPTZ NOT NULL,
    actual_start_utc TIMESTAMPTZ,
    actual_end_utc TIMESTAMPTZ,
    rows_written INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'completed',
    started_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at_utc TIMESTAMPTZ,
    notes JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS market_data.observations (
    series_id BIGINT NOT NULL REFERENCES market_data.series (series_id) ON DELETE CASCADE,
    observation_time_utc TIMESTAMPTZ NOT NULL,
    close_price DOUBLE PRECISION NOT NULL,
    ingestion_run_id BIGINT NOT NULL REFERENCES market_data.ingestion_runs (ingestion_run_id) ON DELETE RESTRICT,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (series_id, observation_time_utc)
);

CREATE INDEX IF NOT EXISTS idx_series_lookup
    ON market_data.series (source_name, timeframe);

CREATE INDEX IF NOT EXISTS idx_observations_time
    ON market_data.observations (observation_time_utc);
