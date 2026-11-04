import math

from engine.pose.types import Landmark


def is_usable_landmark(
    landmark: Landmark,
    visibility_threshold: float = 0.5,
) -> bool:
    if not 0.0 <= visibility_threshold <= 1.0:
        raise ValueError("visibility_threshold must be between 0 and 1")

    return (
        landmark.visibility >= visibility_threshold
        and math.isfinite(landmark.x)
        and math.isfinite(landmark.y)
        and math.isfinite(landmark.z)
        and math.isfinite(landmark.visibility)
    )


def valid_frame_ratio(valid_mask: list[bool]) -> float:
    if not valid_mask:
        return 0.0

    return sum(valid_mask) / len(valid_mask)
