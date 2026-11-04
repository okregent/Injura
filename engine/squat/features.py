from dataclasses import dataclass
from typing import Dict, List, Optional

from engine.biomechanics.angles import (
    calculate_angle,
    calculate_angle_from_vertical,
)
from engine.biomechanics.distance import euclidean_distance_2d
from engine.pose.accessors import get_landmark
from engine.pose.side import BodySide, side_landmarks
from engine.pose.types import Landmark, PoseSequence
from engine.squat.quality import is_usable_landmark, valid_frame_ratio


OptionalFloatSequence = List[Optional[float]]
OptionalLandmarkSequence = List[Optional[Landmark]]


@dataclass
class SquatFeatures:
    side: BodySide
    visibility_threshold: float
    hip_y_values: OptionalFloatSequence
    torso_angles: OptionalFloatSequence
    knee_angles: OptionalFloatSequence
    hip_angles: OptionalFloatSequence
    knee_landmarks: OptionalLandmarkSequence
    toe_landmarks: OptionalLandmarkSequence
    heel_y_values: OptionalFloatSequence
    foot_lengths: OptionalFloatSequence
    valid_masks: Dict[str, List[bool]]

    @property
    def frame_count(self) -> int:
        return len(self.hip_y_values)

    def valid_ratio(self, feature_name: str) -> float:
        try:
            mask = self.valid_masks[feature_name]
        except KeyError as error:
            raise ValueError(f"unsupported feature_name: {feature_name}") from error

        return valid_frame_ratio(mask)


def _all_usable(
    landmarks: List[Landmark],
    visibility_threshold: float,
) -> bool:
    return all(
        is_usable_landmark(landmark, visibility_threshold)
        for landmark in landmarks
    )


def _safe_flexion_angle(
    a: Landmark,
    b: Landmark,
    c: Landmark,
) -> Optional[float]:
    try:
        return 180.0 - calculate_angle(a, b, c)
    except ValueError:
        return None


def _safe_vertical_angle(
    start: Landmark,
    end: Landmark,
) -> Optional[float]:
    try:
        return calculate_angle_from_vertical(start, end)
    except ValueError:
        return None


def extract_squat_features(
    pose_sequence: PoseSequence,
    side: BodySide,
    visibility_threshold: float = 0.5,
    *,
    image_size: tuple[int, int],
) -> SquatFeatures:
    """Extract features from image-normalized landmarks.

    ``image_size`` is the source (width, height) in pixels. Geometry uses image
    width as a common unit; positional outputs retain their original normalized
    coordinates. Joint flexion is zero at extension and increases with bending.
    """
    if not 0.0 <= visibility_threshold <= 1.0:
        raise ValueError("visibility_threshold must be between 0 and 1")

    if len(image_size) != 2 or any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
        for value in image_size
    ):
        raise ValueError("image_size must contain positive integer width and height")
    width, height = image_size

    def geometry_landmark(landmark: Landmark) -> Landmark:
        return Landmark(
            x=landmark.x,
            y=landmark.y * (height / width),
            z=landmark.z,
            visibility=landmark.visibility,
        )

    landmarks_for_side = side_landmarks(side)

    hip_y_values: OptionalFloatSequence = []
    torso_angles: OptionalFloatSequence = []
    knee_angles: OptionalFloatSequence = []
    hip_angles: OptionalFloatSequence = []
    knee_landmarks: OptionalLandmarkSequence = []
    toe_landmarks: OptionalLandmarkSequence = []
    heel_y_values: OptionalFloatSequence = []
    foot_lengths: OptionalFloatSequence = []

    for frame in pose_sequence:
        shoulder = get_landmark(frame, landmarks_for_side["shoulder"])
        hip = get_landmark(frame, landmarks_for_side["hip"])
        knee = get_landmark(frame, landmarks_for_side["knee"])
        ankle = get_landmark(frame, landmarks_for_side["ankle"])
        heel = get_landmark(frame, landmarks_for_side["heel"])
        toe = get_landmark(frame, landmarks_for_side["toe"])

        hip_valid = is_usable_landmark(hip, visibility_threshold)
        knee_valid = is_usable_landmark(knee, visibility_threshold)
        toe_valid = is_usable_landmark(toe, visibility_threshold)
        heel_valid = is_usable_landmark(heel, visibility_threshold)

        hip_y_values.append(hip.y if hip_valid else None)
        knee_landmarks.append(knee if knee_valid else None)
        toe_landmarks.append(toe if toe_valid else None)
        heel_y_values.append(heel.y if heel_valid else None)

        shoulder, hip, knee, ankle, heel, toe = [
            geometry_landmark(landmark)
            for landmark in (shoulder, hip, knee, ankle, heel, toe)
        ]

        if _all_usable([hip, shoulder], visibility_threshold):
            torso_angles.append(_safe_vertical_angle(hip, shoulder))
        else:
            torso_angles.append(None)

        if _all_usable([hip, knee, ankle], visibility_threshold):
            knee_angles.append(_safe_flexion_angle(hip, knee, ankle))
        else:
            knee_angles.append(None)

        if _all_usable([shoulder, hip, knee], visibility_threshold):
            hip_angles.append(_safe_flexion_angle(shoulder, hip, knee))
        else:
            hip_angles.append(None)

        if heel_valid and toe_valid:
            foot_length = euclidean_distance_2d(heel, toe)
            foot_lengths.append(foot_length if foot_length > 0 else None)
        else:
            foot_lengths.append(None)

    valid_masks = {
        "hip_y": [value is not None for value in hip_y_values],
        "torso_angle": [value is not None for value in torso_angles],
        "knee_angle": [value is not None for value in knee_angles],
        "hip_angle": [value is not None for value in hip_angles],
        "knee": [value is not None for value in knee_landmarks],
        "toe": [value is not None for value in toe_landmarks],
        "heel_y": [value is not None for value in heel_y_values],
        "foot_length": [value is not None for value in foot_lengths],
    }

    return SquatFeatures(
        side=side,
        visibility_threshold=visibility_threshold,
        hip_y_values=hip_y_values,
        torso_angles=torso_angles,
        knee_angles=knee_angles,
        hip_angles=hip_angles,
        knee_landmarks=knee_landmarks,
        toe_landmarks=toe_landmarks,
        heel_y_values=heel_y_values,
        foot_lengths=foot_lengths,
        valid_masks=valid_masks,
    )
