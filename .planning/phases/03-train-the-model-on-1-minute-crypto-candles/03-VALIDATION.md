---
phase: 03
slug: train-the-model-on-1-minute-crypto-candles
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-16
---

# Phase 03 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python -m pytest --collect-only -q tests/test_postgres_prepare_training_source.py tests/test_training_manifest.py tests/test_training_preparer.py tests/test_training_workflow.py tests/test_training_lineage.py` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run the smallest plan-local pytest target touched by the task. If a change spans source readiness, bundle preparation, workflow, and lineage boundaries, run the quick collect-only smoke command first and then the smallest meaningful `-x` task target.
- **After every plan wave:** Run `python -m pytest -q tests/test_postgres_prepare_training_source.py tests/test_training_manifest.py tests/test_training_preparer.py tests/test_training_workflow.py tests/test_training_lineage.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | MODEL-01, MODEL-02 | T-03-01 / T-03-03 | Source readiness rejects unsupported symbols, incomplete coverage, and blocking minute-gap segments before preparation starts | integration | `python -m pytest -q tests/test_postgres_prepare_training_source.py -x` | no - W0 | pending |
| 03-02-01 | 02 | 2 | MODEL-02 | T-03-04 / T-03-06 | Manifest validation and preparer output preserve explicit train/holdout boundaries and machine-readable quality reporting | integration/contract | `python -m pytest -q tests/test_training_manifest.py tests/test_training_preparer.py -x` | no - W0 | pending |
| 03-03-01 | 03 | 3 | MODEL-01, OPS-01 | T-03-07 / T-03-09 | Manual training wrapper requires an explicit parent checkpoint and records frozen environment plus run metadata in one deterministic directory | integration | `python -m pytest -q tests/test_training_workflow.py -x` | no - W0 | pending |
| 03-04-01 | 04 | 4 | MODEL-01, OPS-01 | T-03-10 / T-03-12 | Lineage and comparison outputs attach eval/backtest summaries to each run and make cross-run differences traceable | contract | `python -m pytest -q tests/test_training_lineage.py -x` | no - W0 | pending |

*Status: pending, green, red, flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_postgres_prepare_training_source.py` - source coverage targets, allowed symbol scope, segment-aware integrity findings, and readiness blocking behavior
- [ ] `tests/test_training_manifest.py` - manifest schema validation, explicit holdout boundaries, preset helpers, and copied config metadata
- [ ] `tests/test_training_preparer.py` - fixed-length 640-point window emission, strict vs repair handling, and quality report fields
- [ ] `tests/test_training_workflow.py` - wrapper invocation, explicit parent-checkpoint capture, deterministic run-bundle layout, and environment snapshot coverage
- [ ] `tests/test_training_lineage.py` - per-run summary artifacts, backtest-run linkage, and cross-run comparison coverage
- [ ] Extend PostgreSQL fixtures to seed BTC, ETH, and SOL minute data with short-gap, long-gap, and missing-symbol cases
- [ ] Capture the supported Phase 3 training environment in `requirements.training.txt` before runtime verification depends on live installs

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The documented Phase 3 workflow can train from a prepared PostgreSQL-derived bundle in the supported runtime | MODEL-01, MODEL-02 | The legacy TimesFM v1 JAX/PAX stack depends on environment-specific GPU, CUDA, and driver compatibility that unit tests cannot certify | Build the documented Phase 3 environment, create one prepared bundle for BTCUSDT, ETHUSDT, and SOLUSDT, run the training wrapper, and confirm the checkpoint plus run manifest are created under the expected run directory |
| Cross-run reports remain interpretable after a manual training run | MODEL-01, OPS-01 | Automated tests can pin artifact presence and schema, but not operator readability of the final comparison report | Run at least two Phase 3 training workflows, link them to any referenced PostgreSQL backtest runs, and confirm the generated comparison report clearly shows parent checkpoint, dataset ranges, holdouts, preparer settings, and referenced backtest IDs |

---

## Validation Sign-Off

- [ ] All plans have automated verify commands or Wave 0 additions covering their first task
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all Phase 3 test-file gaps
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` remains accurate as plans evolve

**Approval:** pending
