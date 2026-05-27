from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SquatPhaseThresholds:
    standing_y: float
    bottom_y: float
    velocity_threshold: float

def calculate_squat_phase_thresholds(
        hip_y_values: List[float],
        velocity_threshold_ratio: float = 0.03,
) -> SquatPhaseThresholds:
    if not hip_y_values:
        raise ValueError("hip_y_values list cannot be empty")
    
    standing_y = min(hip_y_values)
    bottom_y = max(hip_y_values)

    movement_range = bottom_y - standing_y

    if movement_range <= 0:
        raise ValueError("Invalid hip_y_values: bottom_y must be greater than standing_y")

    velocity_threshold = movement_range * velocity_threshold_ratio

    return SquatPhaseThresholds(
        standing_y=standing_y,
        bottom_y=bottom_y,
        velocity_threshold=velocity_threshold
    )


class SquatPhase(Enum):
    STANDING = auto()
    DESCENDING = auto()
    BOTTOM = auto()
    ASCENDING = auto()
    LOCKOUT = auto()
    UNKNOWN = auto()


def detect_squat_phase(
    current_hip_y: float,
    previous_hip_y: float,
    thresholds: SquatPhaseThresholds,
    standing_zone_ratio = 0.15,
    bottom_zone_ratio = 0.85
) -> SquatPhase:

    hip_velocity = current_hip_y - previous_hip_y
    movement_range = thresholds.bottom_y - thresholds.standing_y

    standing_zone = thresholds.standing_y + movement_range * standing_zone_ratio
    bottom_zone = thresholds.standing_y + movement_range * bottom_zone_ratio

    # descending
    if hip_velocity > thresholds.velocity_threshold:
        return SquatPhase.DESCENDING

    # ascending
    if hip_velocity < -thresholds.velocity_threshold:
        return SquatPhase.ASCENDING

    # bottom
    if current_hip_y >= bottom_zone:
        return SquatPhase.BOTTOM

    # standing / lockout
    if current_hip_y <= standing_zone:
        return SquatPhase.STANDING

    return SquatPhase.UNKNOWN

def detect_squat_phases(
        hip_y_values: List[float],
        thresholds: Optional[SquatPhaseThresholds] = None,
) -> List[SquatPhase]:
    
    if len(hip_y_values) < 2:
        raise ValueError("At least two hip_y_values are required to detect squat phases")   
    
    if thresholds is None:
        thresholds = calculate_squat_phase_thresholds(hip_y_values)

    phases = [SquatPhase.UNKNOWN] # First frame has no previous frame to compare to

    for i in range(1, len(hip_y_values)):
        phase = detect_squat_phase(
            current_hip_y=hip_y_values[i],
            previous_hip_y=hip_y_values[i - 1],
            thresholds=thresholds
        )
        phases.append(phase)

    return phases

@dataclass
class SquatRep:
    start_index: int
    bottom_index: int
    end_index: int

def detect_squat_reps(phases: list[SquatPhase]) -> list[SquatRep]:
    reps = []

    in_rep = False
    start_index = None
    bottom_index = None

    for i, phase in enumerate(phases):
        if not in_rep and phase == SquatPhase.DESCENDING:
            in_rep = True
            start_index = i
            bottom_index = None

        elif in_rep and phase == SquatPhase.BOTTOM:
            bottom_index = i

        elif in_rep and phase in (SquatPhase.ASCENDING, SquatPhase.LOCKOUT, SquatPhase.STANDING):
            if bottom_index is not None and phase in (SquatPhase.LOCKOUT, SquatPhase.STANDING):
                reps.append(
                    SquatRep(
                        start_index=start_index,
                        bottom_index=bottom_index,
                        end_index=i,
                    )
                )
                in_rep = False
                start_index = None
                bottom_index = None

    return reps

            