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


def test_direction_guess_correct_tracks_side_of_last_input_close() -> None:
    metrics = load_metrics_module()

    assert metrics.direction_guess_correct(
        last_input_close=100.0,
        predicted_close=112.0,
        actual_close=110.0,
    ) == 1
    assert metrics.direction_guess_correct(
        last_input_close=100.0,
        predicted_close=88.0,
        actual_close=90.0,
    ) == 1
    assert metrics.direction_guess_correct(
        last_input_close=100.0,
        predicted_close=112.0,
        actual_close=90.0,
    ) == 0
    assert metrics.direction_guess_correct(
        last_input_close=100.0,
        predicted_close=100.0,
        actual_close=100.0,
    ) == 1


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


def test_absolute_move_pct_from_input_uses_last_input_close_as_reference() -> None:
    metrics = load_metrics_module()

    assert metrics.absolute_move_pct_from_input(
        last_input_close=100.0,
        close_value=103.0,
    ) == pytest.approx(3.0)
    assert metrics.absolute_move_pct_from_input(
        last_input_close=100.0,
        close_value=97.5,
    ) == pytest.approx(2.5)


def test_conditional_direction_move_thresholds_lock_step_specific_defaults() -> None:
    metrics = load_metrics_module()

    expected = {
        1: {
            "baseline_deviation_pct": 0.039886,
            "lower_threshold_pct": 0.019886,
            "upper_threshold_pct": 0.059886,
        },
        2: {
            "baseline_deviation_pct": 0.057832,
            "lower_threshold_pct": 0.037832,
            "upper_threshold_pct": 0.077832,
        },
        3: {
            "baseline_deviation_pct": 0.070966,
            "lower_threshold_pct": 0.050966,
            "upper_threshold_pct": 0.090966,
        },
        4: {
            "baseline_deviation_pct": 0.081788,
            "lower_threshold_pct": 0.061788,
            "upper_threshold_pct": 0.101788,
        },
        5: {
            "baseline_deviation_pct": 0.091254,
            "lower_threshold_pct": 0.071254,
            "upper_threshold_pct": 0.111254,
        },
    }

    assert metrics.DEFAULT_CONDITIONAL_DIRECTION_MOVE_THRESHOLDS_PCT == expected
    assert {
        step_ahead: metrics.conditional_direction_move_thresholds(step_ahead)
        for step_ahead in range(1, 6)
    } == expected


def test_conditional_direction_move_thresholds_reject_unsupported_steps() -> None:
    metrics = load_metrics_module()

    with pytest.raises(ValueError, match="step_ahead must be one of 1, 2, 3, 4, or 5"):
        metrics.conditional_direction_move_thresholds(6)


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
        "direction_guess_correct": 1,
    }
