from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List

from .types import CalibrationBucket, CalibrationSummary, SettledPrediction


def brier_score(predictions: Iterable[SettledPrediction]) -> float:
    rows = list(predictions)
    if not rows:
        return 0.0
    return sum(
        (row.predicted_up_probability - row.actual_up_outcome) ** 2
        for row in rows
    ) / len(rows)


def bucket_calibration(
    predictions: Iterable[SettledPrediction],
    bucket_size_percent: int = 5,
) -> List[CalibrationBucket]:
    rows = list(predictions)
    buckets = defaultdict(lambda: {"predicted_sum": 0.0, "actual_sum": 0.0, "count": 0})

    for row in rows:
        bin_start = int(row.predicted_up_probability * 100 // bucket_size_percent) * bucket_size_percent
        bin_end = bin_start + bucket_size_percent
        key = f"{bin_start}-{bin_end}%"
        buckets[key]["predicted_sum"] += row.predicted_up_probability
        buckets[key]["actual_sum"] += row.actual_up_outcome
        buckets[key]["count"] += 1

    result = []
    for key in sorted(buckets.keys()):
        item = buckets[key]
        result.append(
            CalibrationBucket(
                bucket=key,
                predicted_avg=item["predicted_sum"] / item["count"],
                actual_rate=item["actual_sum"] / item["count"],
                count=item["count"],
            )
        )
    return result


def summarize_calibration(predictions: Iterable[SettledPrediction]) -> CalibrationSummary:
    rows = list(predictions)
    if not rows:
        return CalibrationSummary(
            total_predictions=0,
            total_with_outcome=0,
            accuracy=0.0,
            avg_predicted_edge=0.0,
            avg_actual_edge=0.0,
            brier_score=0.0,
        )

    correct = 0
    signed_actual_edges = []
    for row in rows:
        actual_direction = "up" if row.actual_up_outcome >= 0.5 else "down"
        is_correct = row.direction == actual_direction
        if is_correct:
            correct += 1
        signed_actual_edges.append(row.edge if is_correct else -row.edge)

    return CalibrationSummary(
        total_predictions=len(rows),
        total_with_outcome=len(rows),
        accuracy=correct / len(rows),
        avg_predicted_edge=sum(abs(row.edge) for row in rows) / len(rows),
        avg_actual_edge=sum(signed_actual_edges) / len(rows),
        brier_score=brier_score(rows),
    )
