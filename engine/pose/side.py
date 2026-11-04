from enum import Enum

from .landmarks import PoseLandmark


class BodySide(Enum):
    LEFT = "left"
    RIGHT = "right"


def side_landmarks(side: BodySide) -> dict[str, PoseLandmark]:
    if side == BodySide.LEFT:
        return {
            "shoulder": PoseLandmark.LEFT_SHOULDER,
            "hip": PoseLandmark.LEFT_HIP,
            "knee": PoseLandmark.LEFT_KNEE,
            "ankle": PoseLandmark.LEFT_ANKLE,
            "heel": PoseLandmark.LEFT_HEEL,
            "toe": PoseLandmark.LEFT_FOOT_INDEX,
        }

    if side == BodySide.RIGHT:
        return {
            "shoulder": PoseLandmark.RIGHT_SHOULDER,
            "hip": PoseLandmark.RIGHT_HIP,
            "knee": PoseLandmark.RIGHT_KNEE,
            "ankle": PoseLandmark.RIGHT_ANKLE,
            "heel": PoseLandmark.RIGHT_HEEL,
            "toe": PoseLandmark.RIGHT_FOOT_INDEX,
        }

    raise ValueError("unsupported body side")
