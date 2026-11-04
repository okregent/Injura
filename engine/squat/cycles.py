"""Position-based squat state transitions with bottom-exit hysteresis."""

from engine.squat.phases import SquatPhase, SquatPhaseThresholds
from engine.squat.features import SquatFeatures
from statistics import median
import math


def standing_posture_reference(features: SquatFeatures, max_flexion: float = 25.0):
    """Experimental reference from near-extended knees, not a posture diagnosis.

    A median reduces sensitivity to isolated hip-position extrema during setup.
    Require at least five valid samples; otherwise report no usable reference.
    The threshold is an engineering proxy requiring independent validation.
    """
    values = [
        y for index, (y, angle) in enumerate(zip(features.hip_y_values, features.knee_angles))
        if y is not None and angle is not None and math.isfinite(y) and math.isfinite(angle)
        and features.valid_masks["hip_y"][index] and features.valid_masks["knee_angle"][index]
        and 0 <= angle <= max_flexion
    ]
    return (median(values), len(values)) if len(values) >= 5 else (None, len(values))


def detect_cycle_phases(values: list[float], thresholds: SquatPhaseThresholds) -> list[SquatPhase]:
    """Require observed standing, then descent/bottom/ascent/standing.

    Maintain direction through small coordinate reversals. Enter bottom at 85%
    of calibrated descent and leave at 75%, preventing boundary chatter. A return
    to bottom after ascent remains explicit, so genuine double dips are not
    silently turned into ordered phases. No filtering or interpolation occurs.
    """
    movement = thresholds.bottom_y - thresholds.standing_y
    if movement <= 0:
        raise ValueError("bottom_y must be greater than standing_y")
    standing = thresholds.standing_y + 0.15 * movement
    bottom_enter = thresholds.standing_y + 0.85 * movement
    bottom_exit = thresholds.standing_y + 0.75 * movement
    state = SquatPhase.UNKNOWN
    result = []
    for value in values:
        if value <= standing:
            state = SquatPhase.STANDING
        elif state == SquatPhase.STANDING:
            # A single jump straight to bottom has no observed descent phase.
            state = SquatPhase.DESCENDING if value < bottom_enter else SquatPhase.UNKNOWN
        elif state == SquatPhase.DESCENDING and value >= bottom_enter:
            state = SquatPhase.BOTTOM
        elif state == SquatPhase.BOTTOM and value <= bottom_exit:
            state = SquatPhase.ASCENDING
        elif state == SquatPhase.ASCENDING and value >= bottom_enter:
            state = SquatPhase.BOTTOM
        result.append(state)
    return result
