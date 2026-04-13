# Codebase Concerns

**Analysis Date:** 2026-04-13

## Tech Debt

**Training configuration is not the source of truth:**
- Files: `src/main.py`, `configs/fine_tuning.py`
- Issue: `src/main.py` hard-codes `context_len=512`, `horizon_len=128`, `output_patch_len=128`, `backend='gpu'`, and the base checkpoint while the repository advertises `configs/fine_tuning.py` as the place to control training.
- Why: The entrypoint is still wired like an experiment harness instead of a config-driven launcher.
- Impact: Fine-tuning runs are hard to reproduce, config edits can be ignored silently, and the unresolved `# TODO` on horizon length means larger-horizon experiments do not have a safe path.
- Fix approach: Move model/runtime fields into `configs/fine_tuning.py`, validate them in `src/main.py`, and fail fast when an unsupported combination is requested.

**Repository-managed dependency setup only covers inference:**
- Files: `requirements.inference.txt`, `scripts/setup_windows.ps1`, `README.md`, `src/main.py`, `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, `configs/fine_tuning.py`
- Issue: The repo ships a small inference requirements file and bootstrap script, but the documented training/evaluation entrypoints depend on `jax`, `tensorflow`, `paxml`, `praxis`, `clu`, `ml_collections`, `optax`, `flax`, and `orbax` with no pinned installation path in the repository.
- Why: Inference support was productized, while the original fine-tuning code remained closer to research code.
- Impact: Training setup is not reproducible from the repo alone, onboarding is brittle, and dependency drift is likely when someone tries to run `src/main.py`.
- Fix approach: Add a training environment spec separate from inference, pin the full training stack, and align `scripts/setup_windows.ps1` and `README.md` with the supported runtime story.

## Known Bugs

**Directional accuracy drops neutral cases from the confusion matrix:**
- Files: `src/utils.py`, `src/train_flax.py`, `src/train.py`, `src/evaluation.py`
- Symptoms: Accuracy and confusion-matrix-derived metrics undercount samples whenever returns fall inside the neutral threshold band.
- Trigger: Call `get_confusion_matrix(..., num_classes=2)` in `src/utils.py` or `get_conf_matrix(..., num_classes=2)` in `src/train_flax.py`; both paths still classify to class `2` even though the confusion matrix only allocates two classes.
- Workaround: None in code. Manual metric recomputation outside the repository is the only reliable check.
- Root cause: The two-class branch reuses three-way classification logic (`0`, `1`, `2`) and then builds a `2 x 2` confusion matrix.
- Blocked by: Missing automated tests around metric correctness in `src/utils.py`, `src/train.py`, and `src/evaluation.py`.

**Mock trading workflow is not self-contained for external users:**
- Files: `src/mock_trading.py`, `src/mock_trading_utils.py`, `README.md`
- Symptoms: The documented mock-trading path depends on a missing `data_paths` module when `--data_path` is omitted, and the explicit `--data_path` branch returns a raw CSV without the asset-specific indexing/cleanup logic used elsewhere.
- Trigger: Run `python src/mock_trading.py --workdir ... --data_path ...` with a normal CSV, or run without `--data_path`.
- Workaround: Manually pre-shape the CSV exactly as `src/mock_trading.py` expects and avoid the missing `data_paths` branch.
- Root cause: `src/mock_trading_utils.py` still contains PFN-internal assumptions and early-returns raw CSVs for user-supplied paths.
- Blocked by: No reusable public dataset adapter layer in `src/mock_trading_utils.py`.

## Security Considerations

**Runtime model and market-data inputs are trusted without provenance controls:**
- Files: `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`
- Risk: The CLI can fetch arbitrary Hugging Face checkpoints via `--repo-id` and remote market data from Yahoo Finance or Binance without revision pinning, integrity checks, or source allowlisting.
- Current mitigation: HTTPS endpoints and a default checkpoint constant in `src/run_forecast.py`.
- Recommendations: Pin model revisions, add an allowlist for production use, log source metadata into outputs/SQLite, and fail closed on unsupported repo ids.

**Docker backtest wrapper mounts the full repository read-write into the container:**
- Files: `scripts/run_crypto_backtest.ps1`, `Dockerfile`
- Risk: The container receives write access to the whole checkout (`-v "${resolvedRepoRoot}:/workspace"`), so any compromised image or buggy runtime can mutate source files, planning artifacts, and local support files instead of only writing outputs.
- Current mitigation: Local image build plus `--rm` container cleanup.
- Recommendations: Mount only `outputs/` read-write, mount source read-only when possible, and document the trust boundary around locally built images.

## Performance Bottlenecks

**Rolling evaluator performs one model invocation per window:**
- Files: `src/evaluate_forecast.py`
- Problem: `evaluate_series()` calls `model.forecast([context], ...)` inside the window loop instead of batching contexts.
- Measurement: With the repository defaults (`--test-points 128`, `--stride 1`), this is roughly 128 separate forecast calls per series before multi-ticker fan-out.
- Cause: The evaluator reuses the single-series inference path instead of the batched strategy already used in `src/crypto_minute_backtest.py`.
- Improvement path: Batch contexts per ticker, reuse the batched forecast pattern from `run_backtest()`, and keep one post-processing pass for metrics.

**Training/evaluation preprocessing materializes multiple full copies of the dataset in memory:**
- Files: `src/train.py`, `src/train_flax.py`
- Problem: `preprocess_csv()` reads the full CSV into pandas, drops columns, transposes the full frame, shuffles a copied frame, and only then converts to `tf.data`.
- Measurement: Not instrumented in the repo, but each call keeps at least the original frame, the transposed frame, and the shuffled/reset-index copy in memory at once.
- Cause: The input pipeline is pandas-first research code rather than a streaming or chunked loader.
- Improvement path: Define the expected dataset schema, stream rows into tensors without full-frame reshaping where possible, and move shuffling/splitting deeper into `tf.data`.

## Fragile Areas

**`src/crypto_minute_backtest.py` is a monolithic runtime path:**
- Files: `src/crypto_minute_backtest.py`
- Why fragile: One file owns CLI parsing, network I/O, SQLite schema management, batching, metrics, persistence, and console reporting across both `backtest` and `live` modes.
- Common failures: Small changes to fetch logic, schema, or metrics can break unrelated paths because there is no module boundary between ingestion, forecasting, and persistence.
- Safe modification: Split the file into fetch/storage/model/metrics modules first, then change behavior behind narrow interfaces.
- Test coverage: No automated tests target this file, and there are no repository test files for the backtest or live modes.

**Training and evaluation logic is duplicated across separate research paths:**
- Files: `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, `src/utils.py`
- Why fragile: Metric logic, batching assumptions, preprocessing, and model-setup code are partially duplicated instead of shared through one validated abstraction.
- Common failures: A fix in one path can leave another path stale, as shown by the duplicated confusion-matrix bug and duplicated device/setup scaffolding.
- Safe modification: Consolidate shared math and preprocessing into one module with contract tests before changing training or evaluation semantics.
- Test coverage: No unit tests pin the expected behavior of preprocessing, metric math, or horizon handling.

## Scaling Limits

**Crypto backtest scope scales linearly in compute and SQLite storage:**
- Files: `src/crypto_minute_backtest.py`
- Current capacity: The shipped backtest path is scoped to one UTC day of 1-minute candles per run, which produces 913 forecast windows with the default `context_len=512`, `horizon_len=16`, and `stride=1`.
- Limit: Multi-day or multi-symbol studies require repeated full model execution and append one `backtest_runs` row plus one `backtest_predictions` row per window.
- Symptoms at limit: SQLite files grow steadily, reruns become slower to inspect/manage, and historical experiments require external orchestration rather than one native command.
- Scaling path: Partition storage by experiment/date, add archival/retention controls, and separate the forecasting engine from the persistence layer before extending beyond one-day experiments.

**Fine-tuning path is effectively constrained to carefully matched accelerator setups:**
- Files: `src/main.py`, `src/train.py`, `src/evaluation.py`, `configs/fine_tuning.py`
- Current capacity: The checked-in defaults assume `backend='gpu'` in `src/main.py` and `batch_size=1024` in `configs/fine_tuning.py`, with hard failures when process/device divisibility does not line up.
- Limit: Smaller or heterogeneous environments have no adaptive batch sizing, no CPU-first fallback in the main training entrypoint, and no documented reduced-resource profile.
- Symptoms at limit: Runs fail early on device-count checks or on unsupported GPU assumptions instead of degrading to a smaller configuration.
- Scaling path: Make backend and batch sizing config-driven, add reduced-resource presets, and validate hardware compatibility before model construction.

## Dependencies at Risk

**`timesfm` v1 compatibility layer and legacy PAX/JAX stack:**
- Files: `README.md`, `requirements.inference.txt`, `Dockerfile`, `src/run_forecast.py`, `src/main.py`, `src/train.py`, `src/evaluation.py`
- Risk: The repo explicitly targets the old TimesFM v1 API and old checkpoint family, while the training code also depends on legacy PAX/Praxis/PaxML internals that are difficult to install and keep aligned.
- Impact: Dependency upgrades can break either inference compatibility or fine-tuning code, and the repo has no lockfile or automated compatibility test to detect the break early.
- Migration plan: Isolate the model runtime behind a small adapter, pin the full dependency graph for the supported mode, and budget a separate migration effort before adopting newer TimesFM APIs.

## Missing Critical Features

**No public-ready dataset validation layer:**
- Files: `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/train.py`, `src/mock_trading_utils.py`
- Problem: User-provided CSVs are only lightly validated for column presence; training data receives no positivity/range checks before `jnp.log`, and mock-trading data-path inputs bypass asset-specific normalization entirely.
- Current workaround: Manual preprocessing outside the repo plus trial-and-error runs.
- Blocks: Reliable self-service use of custom datasets and safer failure messages for invalid finance inputs.
- Implementation complexity: Medium. A shared schema/validation module and clearer input contracts would cover most of the gap.

**No reproducible training bootstrap path:**
- Files: `README.md`, `requirements.inference.txt`, `scripts/setup_windows.ps1`, `src/main.py`
- Problem: The repo documents fine-tuning but does not provide a maintained requirements file, container, or bootstrap script for the full training stack.
- Current workaround: Manual dependency discovery and environment assembly outside the repository.
- Blocks: Repeatable fine-tuning, onboarding, and CI-style validation of the training path.
- Implementation complexity: Medium to high because the training stack is heavier than inference, but the gap is operationally critical.

## Test Coverage Gaps

**Inference and backtest CLIs are untested:**
- Files: `src/run_forecast.py`, `src/evaluate_forecast.py`, `src/crypto_minute_backtest.py`, `scripts/run_crypto_backtest.ps1`, `scripts/setup_windows.ps1`
- What's not tested: Argument validation, Yahoo/Binance ingestion, batched vs single-window forecasting behavior, SQLite writes, and PowerShell wrapper behavior.
- Risk: Regressions in external-data handling or CLI flags will only show up during manual runs after expensive model startup.
- Priority: High
- Difficulty to test: Medium. Most of the surface can be covered with fixture CSVs and mocked HTTP/model calls.

**Training/evaluation math and data assumptions are untested:**
- Files: `src/train.py`, `src/evaluation.py`, `src/train_flax.py`, `src/utils.py`, `configs/fine_tuning.py`
- What's not tested: Confusion-matrix correctness, preprocessing invariants, horizon handling, device reshaping, log-transform safety, and config-to-runtime wiring.
- Risk: Metric bugs, NaN-producing inputs, and broken configuration paths can ship unnoticed because there is no unit or integration test harness.
- Priority: High
- Difficulty to test: Medium. Most issues are pure-Python/JAX math or config validation and do not require full model weights.

---

*Concerns audit: 2026-04-13*
*Update as issues are fixed or new ones discovered*
