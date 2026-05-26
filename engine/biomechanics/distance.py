from engine.pose.types import Landmark
import math

def euclidean_distance_2d(
        a: Landmark,
        b: Landmark,
) -> float:
    dx = b.x - a.x
    dy = b.y - a.y

    return math.sqrt(dx**2 + dy**2)
    