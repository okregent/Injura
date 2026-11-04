#dataclass is a decorator
#List is to provide type info
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

@dataclass
class Landmark:
    x: float
    y: float    
    z: float
    #Quantifying how accurately the landmarks are detected
    visibility: float

PoseFrame = List[Landmark]
PoseSequence = List[PoseFrame]


@dataclass
class PoseExtractionResult:
    pose_sequence: PoseSequence
    source_frame_indices: List[int]
    source_frame_count: int
    image_size: Optional[Tuple[int, int]] = None
    fps: Optional[float] = None

    def __post_init__(self) -> None:
        if self.fps is not None and (
            isinstance(self.fps, bool) or not math.isfinite(self.fps) or self.fps <= 0
        ):
            raise ValueError("fps must be finite and positive when provided")
        if self.image_size is not None and (
            len(self.image_size) != 2
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value <= 0
                for value in self.image_size
            )
        ):
            raise ValueError("image_size must contain positive integer width and height")

        if len(self.pose_sequence) != len(self.source_frame_indices):
            raise ValueError(
                "pose_sequence and source_frame_indices must have the same length"
            )

        if self.source_frame_count < 0:
            raise ValueError("source_frame_count cannot be negative")

        if any(index < 0 for index in self.source_frame_indices):
            raise ValueError("source_frame_indices cannot contain negative values")

        if any(
            current >= following
            for current, following in zip(
                self.source_frame_indices,
                self.source_frame_indices[1:],
            )
        ):
            raise ValueError("source_frame_indices must be strictly increasing")

        if (
            self.source_frame_indices
            and self.source_frame_indices[-1] >= self.source_frame_count
        ):
            raise ValueError(
                "source_frame_indices must be inside the source frame range"
            )
