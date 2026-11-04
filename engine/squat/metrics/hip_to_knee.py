"""Vertical hip-to-knee separation at the deepest observed frame."""

import math
from dataclasses import dataclass

from engine.squat.features import SquatFeatures
from engine.squat.reps import SquatRep
from .bottom_angles import calculate_bottom_joint_angles


@dataclass
class HipToKneeDepthResult:
    deepest_index: int
    hip_y: float
    knee_y: float
    vertical_gap: float


def calculate_hip_to_knee_depth(features: SquatFeatures, rep: SquatRep) -> HipToKneeDepthResult:
    """Return hip_y - knee_y in image-height units; positive is below the knee.

    These are pose joint centers, not the anatomical hip crease or knee surface.
    Missing knee data at the observed bottom is never replaced by another frame.
    """
    bottom = calculate_bottom_joint_angles(features, rep)
    index = bottom.deepest_index
    if (
        len(features.knee_landmarks) != features.frame_count
        or len(features.valid_masks["knee"]) != features.frame_count
    ):
        raise ValueError("knee landmarks and valid mask must align with features")
    knee = features.knee_landmarks[index]
    if knee is None or not features.valid_masks["knee"][index] or not math.isfinite(knee.y):
        raise ValueError("knee is unavailable at the deepest observed frame")
    return HipToKneeDepthResult(index, bottom.deepest_hip_y, knee.y, bottom.deepest_hip_y - knee.y)
