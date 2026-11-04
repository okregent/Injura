from dataclasses import dataclass
from typing import Optional

from engine.pose.orientation import FacingDirection
from engine.pose.types import Landmark
from engine.squat.features import SquatFeatures
from engine.squat.reps import SquatRep


@dataclass
class KneeTravelResult:
    max_travel: float
    max_travel_index: int
    knee_x: float
    toe_x: float


def calculate_knee_travel(
    knee_landmarks: list[Optional[Landmark]],
    toe_landmarks: list[Optional[Landmark]],
    rep: SquatRep,
    facing_direction: FacingDirection,
    *,
    valid_mask: Optional[list[bool]] = None,
) -> KneeTravelResult:
    """Return maximum signed knee-over-toe travel in image-normalized units.

    A positive value is travel in the facing direction beyond the toe. The
    result is not yet normalized by a body segment and must not be compared
    directly across different camera framing or subject distances.
    Both landmarks must be present and unmasked at the same analysis index.
    """

    if not knee_landmarks:
        raise ValueError("knee_landmarks list cannot be empty")

    if not toe_landmarks:
        raise ValueError("toe_landmarks list cannot be empty")

    if len(knee_landmarks) != len(toe_landmarks):
        raise ValueError(
            "knee_landmarks and toe_landmarks must have the same length"
        )

    if valid_mask is not None and len(valid_mask) != len(knee_landmarks):
        raise ValueError("valid_mask and landmarks must have the same length")

    if facing_direction not in (FacingDirection.LEFT, FacingDirection.RIGHT):
        raise ValueError("unsupported facing_direction")

    if rep.start_index < 0:
        raise ValueError("rep.start_index cannot be negative")

    if rep.start_index > rep.end_index:
        raise ValueError(
            "rep.start_index must not be greater than rep.end_index"
        )

    if rep.end_index >= len(knee_landmarks):
        raise ValueError("rep.end_index is outside landmark range")

    def travel_at(index: int) -> float:
        knee_x = knee_landmarks[index].x
        toe_x = toe_landmarks[index].x

        if facing_direction == FacingDirection.RIGHT:
            return knee_x - toe_x

        if facing_direction == FacingDirection.LEFT:
            return toe_x - knee_x

        raise ValueError("unsupported facing_direction")

    valid_indices = [
        index
        for index in range(rep.start_index, rep.end_index + 1)
        if knee_landmarks[index] is not None
        and toe_landmarks[index] is not None
        and (valid_mask is None or valid_mask[index])
    ]
    if not valid_indices:
        raise ValueError("rep contains no valid knee/toe pairs")

    max_travel_index = max(
        valid_indices,
        key=travel_at,
    )

    knee = knee_landmarks[max_travel_index]
    toe = toe_landmarks[max_travel_index]

    return KneeTravelResult(
        max_travel=travel_at(max_travel_index),
        max_travel_index=max_travel_index,
        knee_x=knee.x,
        toe_x=toe.x,
    )


def calculate_knee_travel_from_features(
    features: SquatFeatures,
    rep: SquatRep,
    facing_direction: FacingDirection,
) -> KneeTravelResult:
    """Measure observed knee travel using valid, same-frame knee/toe pairs.

    Facing direction is independent of the selected body side. Missing frames
    can hide the true maximum; returned indices are never compacted.
    """
    knee_mask = features.valid_masks["knee"]
    toe_mask = features.valid_masks["toe"]
    if (
        len(knee_mask) != len(features.knee_landmarks)
        or len(toe_mask) != len(features.toe_landmarks)
    ):
        raise ValueError("valid masks and landmarks must have the same length")

    return calculate_knee_travel(
        knee_landmarks=features.knee_landmarks,
        toe_landmarks=features.toe_landmarks,
        rep=rep,
        facing_direction=facing_direction,
        valid_mask=[knee and toe for knee, toe in zip(knee_mask, toe_mask)],
    )
