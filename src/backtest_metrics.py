from __future__ import annotations

from typing import Literal, TypedDict


OvershootLabel = Literal["overshoot", "undershoot", "match"]
RelativeToInputLabel = Literal["above", "below", "match"]


class StepMetrics(TypedDict):
    overshoot_label: OvershootLabel
    normalized_deviation_pct: float
    signed_deviation_pct: float
    direction_guess_correct: int


class ConditionalMoveThresholds(TypedDict):
    baseline_deviation_pct: float
    lower_threshold_pct: float
    upper_threshold_pct: float


DEFAULT_CONDITIONAL_DIRECTION_MOVE_THRESHOLDS_PCT: dict[
    int, ConditionalMoveThresholds
] = {
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


def _validate_actual_close(actual_close: float) -> None:
    if actual_close == 0.0:
        raise ValueError("actual_close must be non-zero for percentage metrics.")


def _validate_reference_close(reference_close: float) -> None:
    if reference_close == 0.0:
        raise ValueError("reference close must be non-zero for percentage metrics.")


def normalized_deviation_pct(*, predicted_close: float, actual_close: float) -> float:
    _validate_actual_close(actual_close)
    return abs((predicted_close / actual_close) - 1.0) * 100.0


def absolute_move_pct_from_input(
    *,
    last_input_close: float,
    close_value: float,
) -> float:
    _validate_reference_close(last_input_close)
    return abs((close_value / last_input_close) - 1.0) * 100.0


def conditional_direction_move_thresholds(
    step_ahead: int,
) -> ConditionalMoveThresholds:
    if step_ahead not in DEFAULT_CONDITIONAL_DIRECTION_MOVE_THRESHOLDS_PCT:
        raise ValueError("step_ahead must be one of 1, 2, 3, 4, or 5.")
    return dict(DEFAULT_CONDITIONAL_DIRECTION_MOVE_THRESHOLDS_PCT[step_ahead])


def classify_overshoot(
    *,
    last_input_close: float,
    predicted_close: float,
    actual_close: float,
) -> OvershootLabel:
    if predicted_close == actual_close:
        return "match"

    if actual_close > last_input_close:
        return "overshoot" if predicted_close > actual_close else "undershoot"

    if actual_close < last_input_close:
        return "overshoot" if predicted_close < actual_close else "undershoot"

    return "overshoot" if predicted_close > actual_close else "undershoot"


def classify_relative_to_input(
    *,
    last_input_close: float,
    close_value: float,
) -> RelativeToInputLabel:
    if close_value > last_input_close:
        return "above"
    if close_value < last_input_close:
        return "below"
    return "match"


def direction_guess_correct(
    *,
    last_input_close: float,
    predicted_close: float,
    actual_close: float,
) -> int:
    predicted_label = classify_relative_to_input(
        last_input_close=last_input_close,
        close_value=predicted_close,
    )
    actual_label = classify_relative_to_input(
        last_input_close=last_input_close,
        close_value=actual_close,
    )
    return int(predicted_label == actual_label)


def signed_deviation_pct(
    *,
    last_input_close: float,
    predicted_close: float,
    actual_close: float,
) -> float:
    label = classify_overshoot(
        last_input_close=last_input_close,
        predicted_close=predicted_close,
        actual_close=actual_close,
    )
    if label == "match":
        return 0.0

    magnitude = normalized_deviation_pct(
        predicted_close=predicted_close,
        actual_close=actual_close,
    )
    return magnitude if label == "overshoot" else -magnitude


def build_step_metrics(
    *,
    last_input_close: float,
    predicted_close: float,
    actual_close: float,
) -> StepMetrics:
    overshoot_label = classify_overshoot(
        last_input_close=last_input_close,
        predicted_close=predicted_close,
        actual_close=actual_close,
    )
    return {
        "overshoot_label": overshoot_label,
        "normalized_deviation_pct": normalized_deviation_pct(
            predicted_close=predicted_close,
            actual_close=actual_close,
        ),
        "signed_deviation_pct": signed_deviation_pct(
            last_input_close=last_input_close,
            predicted_close=predicted_close,
            actual_close=actual_close,
        ),
        "direction_guess_correct": direction_guess_correct(
            last_input_close=last_input_close,
            predicted_close=predicted_close,
            actual_close=actual_close,
        ),
    }


__all__ = [
    "ConditionalMoveThresholds",
    "DEFAULT_CONDITIONAL_DIRECTION_MOVE_THRESHOLDS_PCT",
    "absolute_move_pct_from_input",
    "OvershootLabel",
    "RelativeToInputLabel",
    "StepMetrics",
    "build_step_metrics",
    "classify_overshoot",
    "classify_relative_to_input",
    "conditional_direction_move_thresholds",
    "direction_guess_correct",
    "normalized_deviation_pct",
    "signed_deviation_pct",
]
