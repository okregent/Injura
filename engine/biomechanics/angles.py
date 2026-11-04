import math
from engine.pose.types import Landmark
from .vector import to_vector, vector_length, dot_product


def calculate_angle(
    a: Landmark,
    b: Landmark,
    c: Landmark,       
) -> float:
    ba = to_vector(b, a)
    bc = to_vector(b, c)

    dot = dot_product(ba, bc)

    magnitude = (
        vector_length(ba) * vector_length(bc)
    )

    if magnitude == 0:
        raise ValueError("angle landmarks must not produce a zero-length vector")

    cosine = dot / magnitude
    
    cosine = max(-1.0, (min(1.0, cosine)))

    angle_radians = math.acos(cosine)

    return math.degrees(angle_radians)


# Backward-compatible alias for the original misspelled public name.
calcualte_angle = calculate_angle


def calculate_angle_from_vertical(
    start: Landmark,
    end: Landmark,
) -> float:
    dx = end.x - start.x
    dy = end.y - start.y

    if dx == 0 and dy == 0:
        raise ValueError("start and end landmarks must not be identical")

    return math.degrees(math.atan2(abs(dx), abs(dy)))
