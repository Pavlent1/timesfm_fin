from __future__ import annotations

from typing import Literal, TypedDict


OvershootLabel = Literal["overshoot", "undershoot", "match"]


class StepMetrics(TypedDict):
    overshoot_label: OvershootLabel
    normalized_deviation_pct: float
    signed_deviation_pct: float


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
    }


__all__ = [
    "OvershootLabel",
    "StepMetrics",
    "build_step_metrics",
    "classify_overshoot",
    "normalized_deviation_pct",
    "signed_deviation_pct",
]
