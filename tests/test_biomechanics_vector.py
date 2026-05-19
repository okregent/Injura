from engine.pose.types import Landmark
from engine.biomechanics.vector import (
    to_vetor, 
    vector_length,
    dot_product,
)
from engine.pose.accessors import get_landmark
from engine.pose.landmarks import PoseLandmark


def test_to_vector():
    a = Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0)
    b = Landmark(x=3.0, y=4.0, z=0.0, visibility=1.0)

    v = to_vetor(a, b)

    assert v == (3.0, 4.0)

def test_vector_length():
    v = (3.0, 4.0)

    length = vector_length(v)

    assert length == 5.0

def test_dot_product():
    v1 = (1.0, 2.0)
    v2 = (3.0, 4.0)

    dp = dot_product(v1, v2)

    assert dp == 11.0

if __name__ == "__main__":
    test_to_vector()
    test_vector_length()
    test_dot_product()
    print("Biomechanics vector tests passed!")
