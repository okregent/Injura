from typing import Optional
from engine.squat.phases import SquatPhase, detect_squat_phases
from engine.squat.reps import SquatRep, detect_squat_reps
from engine.squat.smoothing import smooth_squat_phases


def detect_rough_movement_window(
    phases: list[SquatPhase],
) -> Optional[tuple[int, int]]:
    start_index = None
    end_index = None

    for i, phase in enumerate(phases):
        if phase == SquatPhase.DESCENDING and start_index is None:
            start_index = i

        if phase == SquatPhase.ASCENDING:
            end_index = i

    if start_index is None or end_index is None:
        return None

    if end_index <= start_index:
        return None

    return start_index, end_index


def detect_squat_analysis_window(
    reps: list[SquatRep],
) -> Optional[tuple[int, int]]:
    if not reps:
        return None

    return reps[0].start_index, reps[-1].end_index


def detect_refined_analysis_window(
    hip_y_values: list[float],
) -> Optional[tuple[int, int]]:
    raw_phases = detect_squat_phases(hip_y_values)
    smoothed_phases = smooth_squat_phases(raw_phases, min_duration=2)

    rough_window = detect_rough_movement_window(smoothed_phases)
    if rough_window is None:
        return None

    rough_start, rough_end = rough_window
    cropped_hip_y = hip_y_values[rough_start:rough_end + 1]

    cropped_phases = detect_squat_phases(cropped_hip_y)
    cropped_smoothed_phases = smooth_squat_phases(cropped_phases, min_duration=2)

    cropped_reps = detect_squat_reps(cropped_smoothed_phases)
    if not cropped_reps:
        return None

    cropped_window = detect_squat_analysis_window(cropped_reps)
    if cropped_window is None:
        return None

    cropped_start, cropped_end = cropped_window

    return (
        rough_start + cropped_start,
        rough_start + cropped_end,
    )
