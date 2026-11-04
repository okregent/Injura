"""Foot-length normalization for observed side-view knee travel."""

import math
from dataclasses import dataclass
from statistics import median
from typing import Optional

from engine.pose.orientation import FacingDirection
from engine.squat.features import SquatFeatures
from engine.squat.reps import SquatRep
from .knee_travel import KneeTravelResult, calculate_knee_travel_from_features


@dataclass(frozen=True)
class KneeTravelRecordingConditions:
    """External review of the recording conditions for this repetition.

    None means unverified. These flags must come from recording review or a
    separately validated view detector, never from landmark visibility alone.
    """

    side_view: Optional[bool] = None
    foot_side_on: Optional[bool] = None


class KneeTravelNormalizationUnavailable(ValueError):
    """An expected exclusion that preserves the raw measurement and its reason."""

    def __init__(self, reason: str, raw_result: KneeTravelResult):
        self.reason = reason
        self.raw_result = raw_result
        super().__init__(f"knee travel normalization unavailable: {reason}")


@dataclass
class NormalizedKneeTravelResult:
    normalized_travel: float
    reference_foot_length: float
    reference_frame_count: int
    raw_result: KneeTravelResult


def calculate_normalized_knee_travel(
    features: SquatFeatures,
    rep: SquatRep,
    facing_direction: FacingDirection,
    *,
    recording_conditions: Optional[KneeTravelRecordingConditions] = None,
) -> NormalizedKneeTravelResult:
    """Divide maximum signed travel by the rep's median valid foot length.

    Both lengths use image-width units. The denominator is fixed within the
    repetition, so the peak index is unchanged. Foot length may come from other
    valid frames in the same repetition when the heel is hidden at the peak.
    This reduces scale dependence but does not correct perspective or foot rotation.
    External confirmation of both side view and side-on foot orientation is
    required. Unverified conditions never produce a normalized value.
    """
    raw_result = calculate_knee_travel_from_features(features, rep, facing_direction)
    conditions = recording_conditions or KneeTravelRecordingConditions()
    if conditions.side_view is False:
        raise KneeTravelNormalizationUnavailable("not_side_view", raw_result)
    if conditions.side_view is not True:
        raise KneeTravelNormalizationUnavailable("side_view_unverified", raw_result)
    if conditions.foot_side_on is False:
        raise KneeTravelNormalizationUnavailable("foot_not_side_on", raw_result)
    if conditions.foot_side_on is not True:
        raise KneeTravelNormalizationUnavailable("foot_orientation_unverified", raw_result)

    foot_mask = features.valid_masks["foot_length"]
    if (
        len(features.foot_lengths) != len(features.knee_landmarks)
        or len(foot_mask) != len(features.foot_lengths)
    ):
        raise ValueError("foot lengths, valid mask, and landmarks must have the same length")

    valid_lengths = [
        length
        for index in range(rep.start_index, rep.end_index + 1)
        for length in [features.foot_lengths[index]]
        if foot_mask[index]
        and length is not None
        and math.isfinite(length)
        and length > 0
    ]
    if not valid_lengths:
        raise ValueError("rep contains no valid positive foot lengths")

    reference_length = median(valid_lengths)
    return NormalizedKneeTravelResult(
        normalized_travel=raw_result.max_travel / reference_length,
        reference_foot_length=reference_length,
        reference_frame_count=len(valid_lengths),
        raw_result=raw_result,
    )
