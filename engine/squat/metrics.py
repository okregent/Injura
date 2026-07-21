from dataclasses import dataclass

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
    hip_y_values: list[float],
    rep: SquatRep,
    thresholds: SquatPhaseThresholds,
) -> SquatDepthResult:
    if not hip_y_values:
        raise ValueError("hip_y_values list cannot be empty")

    if rep.start_index < 0:
        raise ValueError("rep.start_index cannot be negative")

    if rep.start_index > rep.end_index:
        raise ValueError("rep.start_index must not be greater than rep.end_index")

    if rep.end_index >= len(hip_y_values):
        raise ValueError("rep.end_index is outside hip_y_values range")

    movement_range = thresholds.bottom_y - thresholds.standing_y

    if movement_range <= 0:
        raise ValueError("bottom_y must be greater than standing_y")

    deepest_index = max(
        range(rep.start_index, rep.end_index + 1),
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