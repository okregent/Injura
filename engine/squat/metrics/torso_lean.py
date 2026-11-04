from dataclasses import dataclass
from typing import Optional

from engine.squat.features import SquatFeatures
from engine.squat.reps import SquatRep


@dataclass
class TorsoLeanResult:
    max_lean_angle: float
    max_lean_index: int
    standing_angle: float
    lean_change: float


def calculate_torso_lean(
    torso_angles: list[Optional[float]],
    rep: SquatRep,
    *,
    valid_mask: Optional[list[bool]] = None,
) -> TorsoLeanResult:
    """Return maximum torso angle and its change from the rep start frame.

    Angles are expected to be magnitudes in degrees from vertical. The caller
    owns landmark selection, visibility checks, and angle preprocessing.
    Missing or masked frames are skipped without changing analysis indices.
    The rep-start angle must be valid to preserve the change baseline.
    """

    if not torso_angles:
        raise ValueError("torso_angles list cannot be empty")

    if valid_mask is not None and len(valid_mask) != len(torso_angles):
        raise ValueError("valid_mask and torso_angles must have the same length")

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

    valid_indices = [
        index
        for index in range(rep.start_index, rep.end_index + 1)
        if torso_angles[index] is not None
        and (valid_mask is None or valid_mask[index])
    ]
    if not valid_indices:
        raise ValueError("rep contains no valid torso angles")
    if valid_indices[0] != rep.start_index:
        raise ValueError("rep start must have a valid torso angle for the baseline")

    max_lean_index = max(
        valid_indices,
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


def calculate_torso_lean_from_features(
    features: SquatFeatures,
    rep: SquatRep,
) -> TorsoLeanResult:
    """Measure observed torso lean using validated, selected-side features.

    A missing rep-start baseline raises ValueError. Missing interior frames can
    hide the true maximum; the result describes observed valid frames only.
    """
    return calculate_torso_lean(
        torso_angles=features.torso_angles,
        rep=rep,
        valid_mask=features.valid_masks["torso_angle"],
    )
