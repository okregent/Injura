import math
from engine.pose.types import Landmark
from .vector import Vector2D, to_vetor, vector_length, dot_product

def calcualte_angle(
    a: Landmark,
    b: Landmark,
    c: Landmark,       
) -> float:
    ba = to_vetor(b, a)
    bc = to_vetor(b, c)

    dot = dot_product(ba, bc)

    magnitude = (
        vector_length(ba) * vector_length(bc)
    )

    cosine = dot / magnitude
    
    cosine = max(-1.0, (min(1.0, cosine)))

    angle_radians = math.acos(cosine)

    return math.degrees(angle_radians)
