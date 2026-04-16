from __future__ import annotations

from typing import Literal, TypedDict


OvershootLabel = Literal["overshoot", "undershoot", "match"]
RelativeToInputLabel = Literal["above", "below", "match"]


class StepMetrics(TypedDict):
    overshoot_label: OvershootLabel
    normalized_deviation_pct: float
    signed_deviation_pct: float
    direction_guess_correct: int


def _validate_actual_close(actual_close: float) -> None:
    if actual_close == 0.0:
        raise ValueError("actual_close must be non-zero for percentage metrics.")


def normalized_deviation_pct(*, predicted_close: float, actual_close: float) -> float:
    _validate_actual_close(actual_close)
    return abs((predicted_close / actual_close) - 1.0) * 100.0


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
    "OvershootLabel",
    "RelativeToInputLabel",
    "StepMetrics",
    "build_step_metrics",
    "classify_overshoot",
    "classify_relative_to_input",
    "direction_guess_correct",
    "normalized_deviation_pct",
    "signed_deviation_pct",
]
