# Fine-tuning TimesFM on financial data

## Introduction
[TimesFM](https://github.com/google-research/timesfm)  is a time series foundation model released by Google in 2024. This repo contains code following this [work](https://tech.preferred.jp/en/blog/timesfm/) , fine-tuning TimesFM on financial data, aligning towards the task of price prediction.

## Installation
This repository targets the original TimesFM v1 API. As of the current upstream
TimesFM project, the old 1.0/2.0 checkpoints should be used with
`timesfm==1.3.0`. This repo is now wired to that compatibility layer for the
v1 checkpoint family.

The `timesfm` package can only be installed in *Python 3.10* due to package conflicts. Ensure that you have the correct Python version installed, which in conda can be done with 

```bash
conda create -n myenv python=3.10
conda activate myenv
```

and then installing the package:

```bash
pip install timesfm==1.3.0
```

To run the AR1 model in `mock_trading.ipynb`, you will also need the `statsmodels` package. 

## Quick start: run the finance-tuned checkpoint

This repo now includes a minimal inference script at `src/run_forecast.py` and
an optional Windows bootstrap script at `scripts/setup_windows.ps1`.

Important platform note:

- The published finance checkpoint is a JAX/PAX checkpoint
- Native Windows installs hit a `lingvo` dependency wall, so the practical path is Linux, WSL, or Docker
- The Docker path below is the recommended way to run this checkpoint on a Windows host

### Docker quick start

Build the image:

```bash
docker build -t timesfm-fin .
```

Run a forecast and write the output back into this repo:

```bash
docker run --rm -v "${PWD}:/workspace" timesfm-fin --ticker AAPL --period 3y --horizon-len 16 --output-csv /workspace/outputs/aapl_forecast.csv
```

Run a rolling accuracy benchmark across multiple tickers:

```bash
docker run --rm --entrypoint python -v "${PWD}:/workspace" timesfm-fin src/evaluate_forecast.py --tickers AAPL MSFT NVDA --period 5y --horizon-len 16 --test-points 128 --stride 4 --output-csv /workspace/outputs/eval_summary.csv
```

### Manual setup on Linux or WSL

```bash
python -m venv .venv
. .venv/bin/activate
pip install "timesfm[pax]==1.3.0"
pip install -r requirements.inference.txt
python src/run_forecast.py --ticker AAPL --period 3y --horizon-len 16
```

Important notes:

- The default checkpoint is the finance-tuned model: `pfnet/timesfm-1.0-200m-fin`
- `--freq 0` is the correct default for daily-or-higher-frequency financial data
- The finance checkpoint is published under `CC BY-NC-SA 4.0`; review the model card before commercial use
- This is a forecasting demo only, not investment advice

You can also run the model on your own CSV:

```bash
python src/run_forecast.py --csv /path/to/prices.csv --column Close --date-column Date --horizon-len 16
```

Or benchmark a CSV with a rolling backtest:

```bash
python src/evaluate_forecast.py --csv /path/to/prices.csv --column Close --date-column Date --horizon-len 16 --test-points 128
```

The rolling evaluator reports:

- `mae`, `rmse`, `mape_pct`, `smape_pct` over all predicted points
- `step1_mae` and `step1_rmse` for the first step ahead
- `step1_directional_accuracy` and `end_directional_accuracy` for price direction checks

## PostgreSQL Phase 1 data foundation

Phase 1 adds a repo-owned PostgreSQL workflow for storing, inspecting, verifying,
and exporting 1-minute close-price datasets without turning the existing
forecasting and training entrypoints into direct database readers yet.

Start the local database:

```bash
docker compose up -d postgres
```

Apply or re-apply the checked-in schema:

```bash
python src/bootstrap_postgres.py
```

Load the default Binance BTCUSDT 1-minute dataset:

```bash
python src/postgres_ingest_binance.py
```

Inspect what data exists:

```bash
python src/postgres_discover_data.py --source binance --timeframe 1m
```

Run integrity verification:

```bash
python src/postgres_verify_data.py --source binance --timeframe 1m
```

Export one chronological series for the current forecasting scripts:

```bash
python src/postgres_materialize_dataset.py --mode series_csv --source binance --symbol BTCUSDT --timeframe 1m --output-csv outputs/btc_series.csv
```

Export an aligned multi-series matrix for the current `train.py` CSV preprocessing path:

```bash
python src/postgres_materialize_dataset.py --mode training_matrix --source binance --timeframe 1m --output-csv outputs/training_matrix.csv
```

Notes:

- `series_csv` writes `Date` and `Close` columns that `src/run_forecast.py` and `src/evaluate_forecast.py` can read directly.
- `training_matrix` writes numeric-only aligned series columns so the existing `src/train.py` preprocessing flow can consume the export without manual reshaping.
- The PostgreSQL service is a local development dependency, not a hosted or shared production service.
- Schema details live in `db/README.md`.

## Crypto minute backtest with PostgreSQL

Phase 2 moves the crypto minute backtest onto the same PostgreSQL store used by
the dataset foundation. The canonical flow is:

1. start the local PostgreSQL service
2. apply the checked-in schema
3. ingest the source Binance dataset into PostgreSQL
4. run the backtest against PostgreSQL-backed candles
5. inspect per-step statistics in `market_data.backtest_step_stats_vw`

Backtest example:

```bash
python src/crypto_minute_backtest.py --day 2026-04-11 --context-len 512 --horizon-len 16 --batch-size 64
```

The backtest reads one UTC day of `binance` / `BTCUSDT` / `1m` candles from the
Phase 1 PostgreSQL tables and writes run metadata, per-window facts, and
per-step prediction metrics back into PostgreSQL through the shared Phase 2
helpers.

Inspect per-step stats for one stored run:

```sql
SELECT *
FROM market_data.backtest_step_stats_vw
WHERE run_id = 1
ORDER BY step_index;
```

From the VS Code terminal on Windows, the PowerShell wrapper below builds the
Docker image if needed and runs the backtest from your current repo checkout.
The wrapper injects PostgreSQL connection settings into the container, uses
`POSTGRES_HOST=host.docker.internal`, and adds the Docker host mapping needed
for Linux-compatible host-gateway routing:

```powershell
.\scripts\run_crypto_backtest.ps1 -Day 2026-04-11
```

You can pass the main tuning knobs directly from the terminal as well:

```powershell
.\scripts\run_crypto_backtest.ps1 -Day 2026-04-11 -Symbol BTCUSDT -ContextLen 512 -HorizonLen 16 -BatchSize 64
```

Live mode still fetches the latest Binance candles, but it persists those
freshly fetched rows into PostgreSQL before forecasting so the database remains
the single canonical store:

```bash
python src/crypto_minute_backtest.py --mode live --context-len 512 --horizon-len 16 --output-csv outputs/live_forecast.csv
```

Runtime note:

- The model load uses the same TimesFM runtime as `src/run_forecast.py`, so you still need a working `timesfm[pax]==1.3.0` or equivalent supported environment such as Linux, WSL, or Docker

## Data
The fine-tuning dataset is proprietary and not publicly available. However, you can download the necessary data using the following APIs:

- [Binance API](https://github.com/binance/binance-public-data/tree/master/python)
- [Yahoo Finance API](https://pypi.org/project/yfinance/)

## Fine-Tuning on Financial Data
To run the code in this repository, use the following command:

```bash
python src/main.py --workdir=/path/to/workdir --config=configs/fine_tuning.py --dataset_path=/path/to/dataset
```

Replace `/path/to/workdir` and `/path/to/dataset` with your local paths.
Logs, tensorboard data and checkpoints will be stored in `workdir`.
`configs/fine_tuning.py` contains the necessary configurations for fine-tuning. A brief summary of the hyperparameter settings is found here:

| Hyperparameter/Architecture    | Setting                           |
|--------------------------------|-----------------------------------|
| Optimizer                      | SGD                               |
| Linear warmup epochs           | 5 |
| Total epochs                   | 100 |
| Peak learning rate             | 1e-4                              |
| Momentum                       | 0.9                               |
| Gradient clip (max norm)       | 1.0                               |
| Batch size                     | 1024                              |
| Max context length             | 512                               |
| Min context length             | 128                               |
| Output length                  | 128                               |
| Layers                         | 20                                |
| Hidden dimensions              | 1280                              |

## Phase 3 manual training workflow

Phase 3 adds a reproducible wrapper around the legacy trainer so manual runs can
point back to an explicit prepared bundle, parent checkpoint, copied config, and
post-train holdout summaries.

1. Prepare a PostgreSQL-backed training bundle:

```bash
python src/postgres_prepare_training.py --manifest outputs/training_manifest.json --output-dir outputs/prepared_bundle
```

2. Launch a manual run from that prepared bundle with an explicit parent checkpoint:

```bash
python src/train_from_postgres.py --bundle-dir outputs/prepared_bundle --output-root outputs/training_runs --parent-checkpoint pfnet/timesfm-1.0-200m-fin --run-name starter-run
```

This writes a deterministic run bundle under `outputs/training_runs/runs/<run-name>/`
with:

- `run_manifest.json`
- copied `inputs/fine_tuning.py` with a bundle-compatible batch size
- `environment_snapshot.json`
- `evaluation_summary.json`
- `backtest_summary.json`

The wrapper keeps the workflow manual-only and treats the trainer's internal
shuffle eval as non-canonical. Use the explicit holdout outputs above for later
comparison.

3. Compare two or more completed run bundles:

```bash
python src/compare_training_runs.py --run-dir outputs/training_runs/runs/run-a --run-dir outputs/training_runs/runs/run-b --output-dir outputs/training_runs/comparison
```

This writes:

- `comparison_summary.json`
- `comparison_summary.md`

The comparison step makes parent checkpoint, prepared-bundle identity, holdout
ranges, evaluation summaries, and referenced `backtest_run_id` values visible in
one report instead of comparing anonymous checkpoint folders by hand.

## Mock trading
We provide our mock trading script and notebook used in calculating several evaluation metrics. To run the mock trading script, use the following command 

```bash
python src/mock_trading.py --workdir=/path/to/workdir --data_path=/path/to/dataset
```
where `workdir` is where the `positions.csv` file, representing the buy/sell orders of each day, will be stored. `data_path` is the path to your test dataset location. `mock_trading_utils.py` contains some data loading functions but is mainly for PFN internal usage. Please adapt this to your own data cleansing needs. 

## Key benchmarks
For reference, we provide some key performance benchmarks attained by our experimental runs.
We are able to achieve around a 30% of overall train/eval loss reduction. On our test set, we achieve the following performance on S&P500. 

| Horizon | Ann Sharpe | Max Drawdown | Ann Returns | Ann Volatility | Neutral Cost (%) |
|---------|------------|--------------|-------------|----------------|------------------|
| 2       | 0.516     | -0.0015      | 0.0125      | 0.0242         | 0.0025           |
| 4       | -0.482     | -0.0283      | -0.0094      | 0.0194         | -0.0055           |
| 8       | 0.227     | -0.0168      | 0.0049      | 0.0215        | 0.0067           |
| 16      | 0.003     | -0.0189      | 0.0001      | 0.0242         | 0.0002           |
| 32      | 0.420     | -0.0155      | 0.0143      | 0.0339         | 0.0804           |
| 64      | 1.285     | -0.0022      | 0.0333      | 0.0260         | 0.3472           |
| 128     | 1.679    | -0.0009      | 0.0361      | 0.0215         | 0.6005           |

The following is a sharpe ratio comparison between our model and traditional benchmarks.
|                | Ours | Original TimesFM | Random | AR1  |
|----------------|------|------------------|--------|------|
| S&P500         | 1.68 | 0.42             | 0.03   | 1.58 |
| TOPIX500       | 1.06 | -1.75            | 0.11   | -0.82|
| Currencies     | 0.25 | -0.04            | -0.03  | 0.88 |
| Crypto Daily   | 0.26 | -0.03            | 0.01   | 0.17 |

## Weights
Pretrained weight is available: https://huggingface.co/pfnet/timesfm-1.0-200m-fin

