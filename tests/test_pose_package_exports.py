from engine.pose import (
    Landmark,
    PoseLandmark,
    get_landmark,
    LEFT_LEG_CHAIN,
)

def test_pose_package_exports():
    frame = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0)
        for _ in range(33)
    ]

    frame[PoseLandmark.LEFT_HIP.value] = Landmark(
        x = 0.5,
        y = 0.6,
        z = 0.0,
        visibility= 0.99,
    )

    left_hip = get_landmark(frame, PoseLandmark.LEFT_HIP)

    assert left_hip.x == 0.5
    assert len(LEFT_LEG_CHAIN) == 3

if __name__ == "__main__":
    test_pose_package_exports()
    print("Pose package exports test passed")