from dataclasses import dataclass
from typing import Optional

from engine.squat.features import SquatFeatures
from engine.squat.phases import SquatPhaseThresholds
from engine.squat.reps import SquatRep


@dataclass
class SquatDepthResult:
    depth_ratio: float
    deepest_index: int
    deepest_hip_y: float
    standing_y: float
    bottom_y: float


def calculate_squat_depth(
    hip_y_values: list[Optional[float]],
    rep: SquatRep,
    thresholds: SquatPhaseThresholds,
    *,
    valid_mask: Optional[list[bool]] = None,
) -> SquatDepthResult:
    """Measure rep descent relative to the calibrated hip movement range.

    This is a within-sequence relative movement metric, not an absolute
    assessment of whether the hip reached a biomechanical depth standard.
    Values are intentionally not clamped to the 0–1 range.
    Missing or masked values are excluded without changing analysis indices.
    With missing frames, the result describes only the observed valid frames.
    """

    if not hip_y_values:
        raise ValueError("hip_y_values list cannot be empty")

    if valid_mask is not None and len(valid_mask) != len(hip_y_values):
        raise ValueError("valid_mask and hip_y_values must have the same length")

    if rep.start_index < 0:
        raise ValueError("rep.start_index cannot be negative")

    if rep.start_index > rep.end_index:
        raise ValueError("rep.start_index must not be greater than rep.end_index")

    if rep.end_index >= len(hip_y_values):
        raise ValueError("rep.end_index is outside hip_y_values range")

    movement_range = thresholds.bottom_y - thresholds.standing_y

    if movement_range <= 0:
        raise ValueError("bottom_y must be greater than standing_y")

    valid_indices = [
        index
        for index in range(rep.start_index, rep.end_index + 1)
        if hip_y_values[index] is not None
        and (valid_mask is None or valid_mask[index])
    ]
    if not valid_indices:
        raise ValueError("rep contains no valid hip y-values")

    deepest_index = max(
        valid_indices,
        key=lambda index: hip_y_values[index],
    )

    deepest_hip_y = hip_y_values[deepest_index]

    depth_ratio = (
        deepest_hip_y - thresholds.standing_y
    ) / movement_range

    return SquatDepthResult(
        depth_ratio=depth_ratio,
        deepest_index=deepest_index,
        deepest_hip_y=deepest_hip_y,
        standing_y=thresholds.standing_y,
        bottom_y=thresholds.bottom_y,
    )


def calculate_squat_depth_from_features(
    features: SquatFeatures,
    rep: SquatRep,
    thresholds: SquatPhaseThresholds,
) -> SquatDepthResult:
    """Measure observed relative depth using validated, selected-side features.

    Thresholds must be calibrated from the same selected-side hip signal.
    Returned indices refer to the original feature sequence, not a filtered list.
    """
    return calculate_squat_depth(
        hip_y_values=features.hip_y_values,
        rep=rep,
        thresholds=thresholds,
        valid_mask=features.valid_masks["hip_y"],
    )
