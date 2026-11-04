from dataclasses import dataclass

from engine.squat.reps import SquatRep


@dataclass
class TorsoLeanResult:
    max_lean_angle: float
    max_lean_index: int
    standing_angle: float
    lean_change: float


def calculate_torso_lean(
    torso_angles: list[float],
    rep: SquatRep,
) -> TorsoLeanResult:
    """Return maximum torso angle and its change from the rep start frame.

    Angles are expected to be magnitudes in degrees from vertical. The caller
    owns landmark selection, visibility checks, and angle preprocessing.
    """

    if not torso_angles:
        raise ValueError("torso_angles list cannot be empty")

    if rep.start_index < 0:
        raise ValueError("rep.start_index cannot be negative")

    if rep.start_index > rep.end_index:
        raise ValueError(
            "rep.start_index must not be greater than rep.end_index"
        )

    if rep.end_index >= len(torso_angles):
        raise ValueError(
            "rep.end_index is outside torso_angles range"
        )

    max_lean_index = max(
        range(rep.start_index, rep.end_index + 1),
        key=lambda index: torso_angles[index],
    )

    max_lean_angle = torso_angles[max_lean_index]
    standing_angle = torso_angles[rep.start_index]
    lean_change = max_lean_angle - standing_angle

    return TorsoLeanResult(
        max_lean_angle=max_lean_angle,
        max_lean_index=max_lean_index,
        standing_angle=standing_angle,
        lean_change=lean_change,
    )
