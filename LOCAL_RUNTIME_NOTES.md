# Local Runtime Notes

This file captures machine-specific runtime facts for this repository so future agents do not need to rediscover them.

## Current Host Setup

- Windows host path: `C:\Users\Pavel\Documents\GitHub\timesfm_fin`
- WSL distro: `Ubuntu 24.04.3 LTS`
- WSL repo path: `/mnt/c/Users/Pavel/Documents/GitHub/timesfm_fin`
- GPU is visible inside WSL via `nvidia-smi`
- PostgreSQL is run from Docker Desktop / Compose on the Windows side

## Important Runtime Boundary

- Native Windows is not the supported training runtime for the TimesFM v1 JAX/PAX stack in this repo.
- The existing Windows `.venv` is usable for repo scripts such as PostgreSQL preparation and bundle generation, but full training fails on native Windows because the `timesfm[pax]` stack needs dependencies such as `lingvo` that are not installable in the current Windows setup.
- Future model training runs should be executed from Linux/WSL or Docker, not from the Windows `.venv`.

## Proven Working Training Runtime

The currently proven training path on this machine is a Linux Docker container with GPU passthrough.

- Container name: `timesfm-train`
- Container working directory: `/workspace`
- Repo mount: `C:\Users\Pavel\Documents\GitHub\timesfm_fin` -> `/workspace`
- Hugging Face cache mount: `C:\Users\Pavel\.cache\huggingface` -> `/root/.cache/huggingface`
- GPU check inside container: `nvidia-smi` works
- JAX check inside container: `python -c "import jax; print(jax.devices())"` shows CUDA

This container was able to install the training stack and complete a real fine-tuning run. If future agents need the shortest path, prefer reusing this container over rebuilding a Windows environment.

## Hugging Face Checkpoint Cache

The finance checkpoint is already cached on the Windows side.

- Windows cache snapshot path:
  `C:\Users\Pavel\.cache\huggingface\hub\models--pfnet--timesfm-1.0-200m-fin\snapshots\bd9703cd3b456cdb0962050cbcd78d5043542184`
- WSL path to the same snapshot:
  `/mnt/c/Users/Pavel/.cache/huggingface/hub/models--pfnet--timesfm-1.0-200m-fin/snapshots/bd9703cd3b456cdb0962050cbcd78d5043542184`

When passing a local parent checkpoint to `src/train_from_postgres.py`, use the WSL path when running inside WSL.

## Data Preparation Status

The recent one-month BTC-only preparation succeeded without redownloading data.

- Manifest:
  `outputs/btc_one_month_manifest.json`
- Prepared bundle:
  `outputs/prepared_btc_one_month`
- Selected slices:
  - train: `2026-02-01T00:00:00Z` -> `2026-03-01T00:00:00Z`
  - holdout/backtest: `2026-03-01T00:00:00Z` -> `2026-04-01T00:00:00Z`

## Known Data Gap

- `BTCUSDT` has one blocking 80-minute gap in the canonical PostgreSQL store:
  `2023-03-24 12:39:00 UTC` -> `2023-03-24 14:00:00 UTC`
- This gap does not block the current one-month BTC experiment because the chosen 2026 slices do not touch it.
- Do not assume the global Phase 3 readiness check means a specific training slice is unusable. The real gate is whether the selected manifest range itself contains blocking gaps.

## Recommended Training Flow

1. Do not use the Windows `.venv` for training.
2. Prefer the existing `timesfm-train` Docker container, or another Linux/WSL Python 3.10 environment.
3. Reuse the prepared bundle from `outputs/prepared_btc_one_month`.
4. Point `--parent-checkpoint` at the local checkpoint bundle directory, not the snapshot root.
5. Run `src/train_from_postgres.py` from Linux/WSL/Docker.

For the current cached finance checkpoint, the correct local parent checkpoint path inside the container is:

`/root/.cache/huggingface/hub/models--pfnet--timesfm-1.0-200m-fin/snapshots/bd9703cd3b456cdb0962050cbcd78d5043542184/checkpoints`

## Dependency Compatibility Note

- `paxml==1.4.0` currently expects `clu==0.0.11`.
- `paxml==1.4.0` also expects `tensorflow~=2.9.2`.
- The training requirements should keep `clu==0.0.11` and a TensorFlow `2.9.x` pin with that PaxML pin.
- If future agents see a `ResolutionImpossible` error around `clu`, check that this compatibility pair has not drifted.

## Notes For Future Agents

- If a user asks to "just train it", first verify whether the request is happening in Windows or WSL.
- If the user is in Windows PowerShell, do not assume the Windows `.venv` can run training just because data preparation works there.
- If training fails on native Windows with missing `clu`, `lingvo`, or other Pax/JAX dependencies, switch to WSL instead of retrying the same Windows install loop.
- `src/train_from_postgres.py` must use the produced checkpoint directory under `run_dir/checkpoints/...`, not the run directory root, for post-train evaluation and backtest.
- A real one-month BTC run already exists at `outputs/training_runs/runs/btc-one-month-run-2ep-b1`.
