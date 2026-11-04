from dataclasses import dataclass

from engine.pose.orientation import FacingDirection
from engine.pose.types import Landmark
from engine.squat.reps import SquatRep


@dataclass
class KneeTravelResult:
    max_travel: float
    max_travel_index: int
    knee_x: float
    toe_x: float


def calculate_knee_travel(
    knee_landmarks: list[Landmark],
    toe_landmarks: list[Landmark],
    rep: SquatRep,
    facing_direction: FacingDirection,
) -> KneeTravelResult:
    """Return maximum signed knee-over-toe travel in image-normalized units.

    A positive value is travel in the facing direction beyond the toe. The
    result is not yet normalized by a body segment and must not be compared
    directly across different camera framing or subject distances.
    """

    if not knee_landmarks:
        raise ValueError("knee_landmarks list cannot be empty")

    if not toe_landmarks:
        raise ValueError("toe_landmarks list cannot be empty")

    if len(knee_landmarks) != len(toe_landmarks):
        raise ValueError(
            "knee_landmarks and toe_landmarks must have the same length"
        )

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

    max_travel_index = max(
        range(rep.start_index, rep.end_index + 1),
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
