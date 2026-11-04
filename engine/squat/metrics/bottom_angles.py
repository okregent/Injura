"""Joint flexion at the deepest observed hip position of a repetition."""

import math
from dataclasses import dataclass
from typing import Optional

from engine.squat.features import SquatFeatures
from engine.squat.reps import SquatRep


@dataclass
class BottomJointAnglesResult:
    deepest_index: int
    deepest_hip_y: float
    knee_flexion_angle: Optional[float]
    hip_flexion_angle: Optional[float]


def calculate_bottom_joint_angles(
    features: SquatFeatures,
    rep: SquatRep,
) -> BottomJointAnglesResult:
    """Return same-frame flexion angles at maximum valid hip y (first tie).

    Missing angles remain None independently; never move to another frame to
    obtain an angle. The deepest observed frame may differ from rep.bottom_index
    and may underestimate depth when hip observations are missing.
    """
    count = features.frame_count
    if not count:
        raise ValueError("hip_y_values list cannot be empty")
    if rep.start_index < 0 or rep.start_index > rep.end_index or rep.end_index >= count:
        raise ValueError("rep indices must define an inclusive range inside features")

    for values, mask_name in (
        (features.hip_y_values, "hip_y"),
        (features.knee_angles, "knee_angle"),
        (features.hip_angles, "hip_angle"),
    ):
        if len(values) != count or len(features.valid_masks[mask_name]) != count:
            raise ValueError("feature values and valid masks must have the same length")

    valid_indices = [
        index
        for index in range(rep.start_index, rep.end_index + 1)
        if features.valid_masks["hip_y"][index]
        and features.hip_y_values[index] is not None
        and math.isfinite(features.hip_y_values[index])
    ]
    if not valid_indices:
        raise ValueError("rep contains no valid hip y-values")
    deepest_index = max(valid_indices, key=lambda index: features.hip_y_values[index])

    def angle_at_bottom(values: list[Optional[float]], mask_name: str) -> Optional[float]:
        value = values[deepest_index]
        if (
            features.valid_masks[mask_name][deepest_index]
            and value is not None
            and math.isfinite(value)
        ):
            return value
        return None

    return BottomJointAnglesResult(
        deepest_index=deepest_index,
        deepest_hip_y=features.hip_y_values[deepest_index],
        knee_flexion_angle=angle_at_bottom(features.knee_angles, "knee_angle"),
        hip_flexion_angle=angle_at_bottom(features.hip_angles, "hip_angle"),
    )
