from engine.pose.types import Landmark
from engine.biomechanics.angles import calcualte_angle


def test_calculate_angle_90():
    a = Landmark(x=0.0, y=1.0, z=0.0, visibility=1.0)
    b = Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0)
    c = Landmark(x=1.0, y=0.0, z=0.0, visibility=1.0)

    angle = calcualte_angle(a, b, c)

    assert round(angle, 2) == 90.0

if __name__ == "__main__":
    test_calculate_angle_90()
    print("Biomechanics angles tests passed!")