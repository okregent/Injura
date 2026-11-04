"""Measurement availability and observed-data coverage (not probability)."""

from dataclasses import dataclass
from typing import Optional

from engine.pose.types import PoseExtractionResult
from engine.squat.features import SquatFeatures
from engine.squat.reps import SquatRep


@dataclass
class MetricQuality:
    valid_frames: int
    expected_frames: int
    coverage: float
    status: str
    reason: Optional[str]


@dataclass
class MetricOutcome:
    value: Optional[object]
    quality: MetricQuality


def assess_metric(
    features: SquatFeatures, extraction: PoseExtractionResult, rep: SquatRep,
    mask_names: list[str], *, available: bool, reason: Optional[str] = None,
) -> MetricQuality:
    """Coverage is valid observations / inclusive source frames in the rep.

    Coverage describes data support only, never calibrated accuracy or medical
    confidence. Even complete coverage does not establish recording suitability.
    """
    source = extraction.source_frame_indices
    expected = source[rep.end_index] - source[rep.start_index] + 1
    valid = sum(
        all(features.valid_masks[name][index] for name in mask_names)
        for index in range(rep.start_index, rep.end_index + 1)
    )
    coverage = valid / expected
    status = "unavailable" if not available else ("available" if coverage == 1 else "partial")
    return MetricQuality(valid, expected, coverage, status, reason)
