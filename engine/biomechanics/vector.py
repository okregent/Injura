from typing import Tuple
from engine.pose.types import Landmark

Vector2D = tuple[float,float]

def to_vetor(a: Landmark, b: Landmark) -> Vector2D:
    return (
        b.x - a.x,
        b.y - a.y,
    )

def vector_length(v: Vector2D) -> float:
    return (v[0]**2 + v[1]**2) ** 0.5

def dot_product(v1: Vector2D, v2:Vector2D) -> float:
    return (v1[0]*v2[0]) + (v1[1]*v2[1])