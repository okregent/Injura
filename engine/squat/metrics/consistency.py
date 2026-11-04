"""Descriptive between-repetition variation, without good/bad thresholds."""

import math
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Optional


@dataclass
class ConsistencyResult:
    valid_count: int
    total_count: int
    mean: Optional[float]
    standard_deviation: Optional[float]
    value_range: Optional[float]


def calculate_consistency(values: list[Optional[float]]) -> ConsistencyResult:
    """Ignore unavailable values; at least two reps are needed for variation.

    Standard deviation is population SD in the original metric units. No CV is
    used because signed knee travel and near-zero means make it misleading.
    """
    valid = [value for value in values if value is not None and math.isfinite(value)]
    return ConsistencyResult(
        len(valid), len(values), mean(valid) if valid else None,
        pstdev(valid) if len(valid) >= 2 else None,
        max(valid) - min(valid) if len(valid) >= 2 else None,
    )
