from engine.pose.types import Landmark
from engine.biomechanics.visibility import (
    is_visible,
    all_visible,
)

def test_is_visible():
    landmark = Landmark(x=0.0, y=0.0, z=0.0, visibility=0.9)

    assert is_visible(landmark)


def test_all_visible():
    landmarks = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=0.9),
        Landmark(x=1.0, y=1.0, z=1.0, visibility=0.8),
        Landmark(x=1.0, y=1.0, z=1.0, visibility=0.4)
    ]

    assert all_visible(landmarks) == False


if __name__ == "__main__":
    test_is_visible()
    test_all_visible()
    print("Biomechanics visibility tests passed!")