from engine.pose.types import Landmark
from engine.biomechanics.temporal import (
    displacement_2d,
    velocity_2d,
)


def test_displacement_2d():
    previous = Landmark(0.0, 0.0, 0.0, 1.0)
    current = Landmark(3.0, 4.0, 0.0, 1.0)

    result = displacement_2d(previous, current)

    assert result == 5.0


def test_velocity_2d():
    previous = Landmark(0.0, 0.0, 0.0, 1.0)
    current = Landmark(3.0, 4.0, 0.0, 1.0)

    result = velocity_2d(
        previous,
        current,
        dt=2.0,
    )

    assert result == 2.5


if __name__ == "__main__":
    test_displacement_2d()
    test_velocity_2d()

    print("Biomechanics temporal tests passed.")