from .types import PoseFrame, Landmark
from .landmarks import PoseLandmark
from typing import List

def get_landmark(frame: PoseFrame, landmark : PoseLandmark) -> Landmark:
    return frame[landmark.value]

def get_landmarks(frame: PoseFrame, landmarks : List[PoseLandmark]) -> List[Landmark]:
    return [get_landmark(frame,landmark)for landmark in landmarks]