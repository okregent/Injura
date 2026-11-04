"""Toe-relative heel-rise proxy in image-height coordinates."""

import math
from dataclasses import dataclass
from typing import Optional

from engine.pose.types import PoseExtractionResult
from engine.squat.features import SquatFeatures
from engine.squat.reps import SquatRep


@dataclass
class HeelLiftResult:
    max_lift: float
    max_lift_index: int
    baseline_toe_minus_heel_y: float
    lifted_seconds: Optional[float]
    timed_coverage: float
    lift_threshold: float


def calculate_heel_lift(
    features: SquatFeatures, rep: SquatRep,
    extraction: Optional[PoseExtractionResult] = None, *, lift_threshold: float = 0.005,
) -> HeelLiftResult:
    """Compare toe_y - heel_y to the valid rep-start baseline.

    Values and threshold use image-height units. The start must have a planted
    foot for physical interpretation. Duration counts only adjacent valid source
    intervals above threshold at their left endpoint; gaps are not interpolated.
    This is a projected rise proxy, not proof of lost ground contact.
    """
    count = features.frame_count
    if not math.isfinite(lift_threshold) or lift_threshold < 0:
        raise ValueError("lift_threshold must be finite and nonnegative")
    if rep.start_index < 0 or rep.end_index >= count or rep.start_index >= rep.end_index:
        raise ValueError("invalid repetition heel-lift range")
    for values, name in ((features.heel_y_values, "heel_y"), (features.toe_landmarks, "toe")):
        if len(values) != count or len(features.valid_masks[name]) != count:
            raise ValueError("heel and toe values and masks must align with features")
    offsets = {}
    for index in range(rep.start_index, rep.end_index + 1):
        heel = features.heel_y_values[index]
        toe = features.toe_landmarks[index]
        if (
            features.valid_masks["heel_y"][index] and features.valid_masks["toe"][index]
            and heel is not None and toe is not None
            and math.isfinite(heel) and math.isfinite(toe.y)
        ):
            offsets[index] = toe.y - heel
    if rep.start_index not in offsets:
        raise ValueError("rep start must have a valid heel/toe baseline")
    baseline = offsets[rep.start_index]
    lifts = {index: max(0.0, value - baseline) for index, value in offsets.items()}
    peak = max(lifts, key=lifts.get)
    duration = None
    coverage = 0.0
    if extraction is not None:
        if len(extraction.pose_sequence) != count:
            raise ValueError("extraction must align with features")
        if extraction.fps is not None:
            source = extraction.source_frame_indices
            timed = [
                index for index in range(rep.start_index, rep.end_index)
                if index in lifts and index + 1 in lifts and source[index + 1] - source[index] == 1
            ]
            elapsed_frames = source[rep.end_index] - source[rep.start_index]
            coverage = len(timed) / elapsed_frames
            if timed:
                duration = sum(lifts[index] > lift_threshold for index in timed) / extraction.fps
    return HeelLiftResult(lifts[peak], peak, baseline, duration, coverage, lift_threshold)
