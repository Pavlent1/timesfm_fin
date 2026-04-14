CREATE TABLE IF NOT EXISTS market_data.backtest_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    model_repo_id TEXT NOT NULL,
    backend TEXT NOT NULL,
    freq_bucket INTEGER NOT NULL,
    context_len INTEGER NOT NULL CHECK (context_len > 0),
    horizon_len INTEGER NOT NULL CHECK (horizon_len > 0),
    stride INTEGER NOT NULL CHECK (stride > 0),
    batch_size INTEGER NOT NULL CHECK (batch_size > 0),
    data_start_utc TIMESTAMPTZ NOT NULL,
    data_end_utc TIMESTAMPTZ NOT NULL,
    points INTEGER NOT NULL CHECK (points >= 0),
    windows INTEGER NOT NULL CHECK (windows >= 0)
);

CREATE TABLE IF NOT EXISTS market_data.backtest_windows (
    window_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES market_data.backtest_runs (run_id) ON DELETE CASCADE,
    window_index INTEGER NOT NULL CHECK (window_index >= 0),
    target_start_utc TIMESTAMPTZ NOT NULL,
    context_end_utc TIMESTAMPTZ NOT NULL,
    last_input_close DOUBLE PRECISION NOT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (run_id, window_index)
);

CREATE TABLE IF NOT EXISTS market_data.backtest_prediction_steps (
    run_id BIGINT NOT NULL REFERENCES market_data.backtest_runs (run_id) ON DELETE CASCADE,
    window_id BIGINT NOT NULL REFERENCES market_data.backtest_windows (window_id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL CHECK (step_index >= 0),
    target_time_utc TIMESTAMPTZ NOT NULL,
    last_input_close DOUBLE PRECISION NOT NULL,
    predicted_close DOUBLE PRECISION NOT NULL,
    actual_close DOUBLE PRECISION NOT NULL,
    normalized_deviation_pct DOUBLE PRECISION NOT NULL,
    signed_deviation_pct DOUBLE PRECISION NOT NULL,
    overshoot_label TEXT NOT NULL CHECK (overshoot_label IN ('overshoot', 'undershoot', 'match')),
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (window_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_backtest_windows_run_id
    ON market_data.backtest_windows (run_id, window_index);

CREATE INDEX IF NOT EXISTS idx_backtest_steps_run_step
    ON market_data.backtest_prediction_steps (run_id, step_index);

CREATE OR REPLACE VIEW market_data.backtest_step_stats_vw AS
SELECT
    run_id,
    step_index,
    COUNT(*)::BIGINT AS step_count,
    AVG(normalized_deviation_pct)::DOUBLE PRECISION AS avg_normalized_deviation_pct,
    COALESCE(STDDEV_POP(normalized_deviation_pct), 0.0)::DOUBLE PRECISION AS stddev_normalized_deviation_pct,
    COUNT(*) FILTER (WHERE overshoot_label = 'overshoot')::BIGINT AS overshoot_count,
    COUNT(*) FILTER (WHERE overshoot_label = 'undershoot')::BIGINT AS undershoot_count,
    COUNT(*) FILTER (WHERE overshoot_label = 'match')::BIGINT AS match_count,
    AVG(signed_deviation_pct)::DOUBLE PRECISION AS avg_signed_deviation_pct
FROM market_data.backtest_prediction_steps
GROUP BY run_id, step_index;
