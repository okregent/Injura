from engine.pose.types import Landmark
from typing import List

def is_visible(
        landmark: Landmark,
        threshold: float = 0.5,
        
    ) -> bool:

    return landmark.visibility >= threshold

def all_visible(
        landmarks: List[Landmark],
        threshold: float = 0.5,
    ) -> bool:

    return all(is_visible(l, threshold) for l in landmarks)
