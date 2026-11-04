"""Explicit human recording review, independent of detector visibility."""

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional

from engine.pose.side import BodySide


@dataclass(frozen=True)
class RecordingReview:
    side: str
    reviewer: Optional[str] = None
    side_view: Optional[bool] = None
    camera_fixed: Optional[bool] = None
    subject_clear: Optional[bool] = None
    hips_visible: Optional[bool] = None
    knees_visible: Optional[bool] = None
    ankles_visible: Optional[bool] = None
    shoulders_visible: Optional[bool] = None
    feet_visible: Optional[bool] = None
    foot_side_on: Optional[bool] = None
    continuous_original_speed: Optional[bool] = None
    constant_frame_rate: Optional[bool] = None
    notes: str = ""

    def __post_init__(self):
        if self.side not in ("left", "right"):
            raise ValueError("review side must be left or right")
        if self.reviewer is not None and (not isinstance(self.reviewer, str) or not self.reviewer.strip()):
            raise ValueError("reviewer must be a nonempty string or null")
        if not isinstance(self.notes, str):
            raise ValueError("review notes must be text")
        for item in fields(self):
            if item.name in ("side", "reviewer", "notes"):
                continue
            value = getattr(self, item.name)
            if value is not None and type(value) is not bool:
                raise ValueError(f"{item.name} must be true, false or null")


REQUIREMENTS = {
    "depth": ("hips_visible",),
    "timing": ("hips_visible", "continuous_original_speed", "constant_frame_rate"),
    "knee_flexion": ("hips_visible", "knees_visible", "ankles_visible"),
    "hip_flexion": ("shoulders_visible", "hips_visible", "knees_visible"),
    "torso_lean": ("shoulders_visible", "hips_visible"),
    "hip_to_knee": ("hips_visible", "knees_visible"),
    "knee_travel": ("knees_visible", "feet_visible"),
    "normalized_knee_travel": ("knees_visible", "feet_visible", "foot_side_on"),
    "heel_lift": ("feet_visible",),
}


def recording_gate(metric, review, side: BodySide):
    """Return approved/unknown/rejected plus a stable reason; no accuracy claim."""
    if review is None:
        return "unknown", "recording_review_missing"
    if not isinstance(review, RecordingReview):
        raise ValueError("recording review must be RecordingReview")
    if review.side != side.value:
        return "unknown", "recording_review_side_mismatch"
    if not review.reviewer:
        return "unknown", "recording_reviewer_missing"
    if metric not in REQUIREMENTS:
        return "unknown", "recording_metric_unsupported"
    requirements = ("side_view", "camera_fixed", "subject_clear") + REQUIREMENTS[metric]
    # A known rejection takes precedence over an additional unknown condition.
    for requirement in requirements:
        if getattr(review, requirement) is False:
            return "rejected", f"recording_review_rejected:{requirement}"
    for requirement in requirements:
        if getattr(review, requirement) is None:
            return "unknown", f"recording_review_unknown:{requirement}"
    return "approved", None


def load_recording_reviews(path, video):
    """Bind side-specific reviews to a source file's name, size and mtime.

    Metadata binding detects ordinary source changes; it is not a content hash.
    In-memory library callers must ensure their reviews belong to their extraction.
    """
    video = Path(video)
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or set(data) != {"video", "size", "mtime_ns", "reviews"}:
        raise ValueError("review file requires video, size, mtime_ns and reviews")
    signature = video.stat()
    if (data["video"] != video.name or type(data["size"]) is not int or type(data["mtime_ns"]) is not int
            or data["size"] != signature.st_size or data["mtime_ns"] != signature.st_mtime_ns):
        raise ValueError("recording review source signature mismatch")
    if not isinstance(data["reviews"], list):
        raise ValueError("reviews must be a list")
    try:
        reviews = [RecordingReview(**item) for item in data["reviews"]]
    except TypeError as error:
        raise ValueError("invalid recording review fields") from error
    if len({review.side for review in reviews}) != len(reviews):
        raise ValueError("duplicate recording review side")
    return reviews
