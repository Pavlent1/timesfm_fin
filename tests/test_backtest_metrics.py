from __future__ import annotations

import importlib

import pytest


def load_metrics_module():
    return importlib.import_module("backtest_metrics")


def test_normalized_deviation_pct_uses_locked_phase2_formula() -> None:
    # Locked formula: abs((predicted_close / actual_close) - 1.0) * 100
    metrics = load_metrics_module()

    predicted_close = 105.0
    actual_close = 100.0

    expected = abs((predicted_close / actual_close) - 1.0) * 100

    assert metrics.normalized_deviation_pct(
        predicted_close=predicted_close,
        actual_close=actual_close,
    ) == pytest.approx(expected)


def test_exact_match_produces_zero_deviation_and_match_label() -> None:
    metrics = load_metrics_module()

    assert metrics.normalized_deviation_pct(
        predicted_close=100.0,
        actual_close=100.0,
    ) == 0.0
    assert metrics.signed_deviation_pct(
        last_input_close=95.0,
        predicted_close=100.0,
        actual_close=100.0,
    ) == 0.0
    assert metrics.classify_overshoot(
        last_input_close=95.0,
        predicted_close=100.0,
        actual_close=100.0,
    ) == "match"


def test_classify_overshoot_for_upward_actual_move() -> None:
    metrics = load_metrics_module()

    last_input_close = 100.0
    actual_close = 110.0

    assert metrics.classify_overshoot(
        last_input_close=last_input_close,
        predicted_close=112.0,
        actual_close=actual_close,
    ) == "overshoot"
    assert metrics.classify_overshoot(
        last_input_close=last_input_close,
        predicted_close=108.0,
        actual_close=actual_close,
    ) == "undershoot"


def test_classify_overshoot_for_downward_actual_move() -> None:
    metrics = load_metrics_module()

    last_input_close = 100.0
    actual_close = 90.0

    assert metrics.classify_overshoot(
        last_input_close=last_input_close,
        predicted_close=88.0,
        actual_close=actual_close,
    ) == "overshoot"
    assert metrics.classify_overshoot(
        last_input_close=last_input_close,
        predicted_close=92.0,
        actual_close=actual_close,
    ) == "undershoot"


def test_signed_deviation_pct_is_positive_for_overshoot_and_negative_for_undershoot() -> None:
    metrics = load_metrics_module()

    upward_overshoot = metrics.signed_deviation_pct(
        last_input_close=100.0,
        predicted_close=112.0,
        actual_close=110.0,
    )
    downward_overshoot = metrics.signed_deviation_pct(
        last_input_close=100.0,
        predicted_close=88.0,
        actual_close=90.0,
    )
    upward_undershoot = metrics.signed_deviation_pct(
        last_input_close=100.0,
        predicted_close=108.0,
        actual_close=110.0,
    )
    downward_undershoot = metrics.signed_deviation_pct(
        last_input_close=100.0,
        predicted_close=92.0,
        actual_close=90.0,
    )

    assert upward_overshoot == pytest.approx((2.0 / 110.0) * 100.0)
    assert downward_overshoot == pytest.approx((2.0 / 90.0) * 100.0)
    assert upward_undershoot == pytest.approx((-2.0 / 110.0) * 100.0)
    assert downward_undershoot == pytest.approx((-2.0 / 90.0) * 100.0)


def test_build_step_metrics_returns_reusable_per_step_inputs() -> None:
    metrics = load_metrics_module()

    step_metrics = metrics.build_step_metrics(
        last_input_close=100.0,
        predicted_close=112.0,
        actual_close=110.0,
    )

    assert step_metrics == {
        "overshoot_label": "overshoot",
        "normalized_deviation_pct": pytest.approx((2.0 / 110.0) * 100.0),
        "signed_deviation_pct": pytest.approx((2.0 / 110.0) * 100.0),
    }
