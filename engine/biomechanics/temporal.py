from engine.pose.types import Landmark
from .distance import euclidean_distance_2d

def displacement_2d(
        previous: Landmark,
        current: Landmark,
) -> float:
    return euclidean_distance_2d(previous, current)

def velocity_2d(
        previous: Landmark,
        current: Landmark,
        dt: float,  # time delta between frames (seconds)
) -> float:
    return displacement_2d(previous, current) / dt
