from engine.pose.types import Landmark
from engine.biomechanics.angles import calculate_angle


def test_calculate_angle_90():
    a = Landmark(x=0.0, y=1.0, z=0.0, visibility=1.0)
    b = Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0)
    c = Landmark(x=1.0, y=0.0, z=0.0, visibility=1.0)

    angle = calculate_angle(a, b, c)

    assert round(angle, 2) == 90.0


def test_calculate_angle_rejects_zero_length_vector():
    repeated = Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0)
    c = Landmark(x=1.0, y=0.0, z=0.0, visibility=1.0)

    try:
        calculate_angle(repeated, repeated, c)
    except ValueError as error:
        assert "zero-length vector" in str(error)
    else:
        raise AssertionError("calculate_angle should reject zero-length vectors")

if __name__ == "__main__":
    test_calculate_angle_90()
    print("Biomechanics angles tests passed!")
