from engine.pose.types import Landmark
from engine.pose.landmarks import PoseLandmark
from engine.pose.accessors import get_landmark, get_landmarks
from engine.pose.chains import LEFT_LEG_CHAIN
def test_get_landmark():
    frame = [
        Landmark(x=0.0, y=0.0, z=0.0,visibility=1.0)
        for _ in range(33)
    ]

    frame[PoseLandmark.LEFT_HIP.value] = Landmark(
        x=0.5,
        y=0.6,
        z=0.0,
        visibility=0.99
    )

    left_hip = get_landmark(frame, PoseLandmark.LEFT_HIP)

    assert left_hip.x == 0.5
    assert left_hip.y == 0.6
    assert left_hip.z == 0.0
    assert left_hip.visibility == 0.99

def test_get_landmarks():
    frame = [
        Landmark(x=0.0, y=0.0, z=0.0,visibility=0.99) for _ in range(33)
    ]

    frame[PoseLandmark.LEFT_HIP.value] = Landmark(
        0.1, 0.2, 0.0, 0.9
    )

    frame[PoseLandmark.LEFT_KNEE.value] = Landmark(
        0.3, 0.4, 0.0, 0.8
    )

    frame[PoseLandmark.LEFT_ANKLE] = Landmark(
        0.5, 0.6, 0.0, 0.7
    )

    left_leg = get_landmarks(frame, LEFT_LEG_CHAIN)

    assert len(left_leg) == 3
    assert left_leg[0].x == 0.1
    assert left_leg[1].x == 0.3
    assert left_leg[2].x == 0.5

if __name__ == "__main__":
    test_get_landmark()
    test_get_landmarks()
    print("Landmark accessor tests passed")