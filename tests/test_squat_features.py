import pytest

from engine.pose.landmarks import PoseLandmark
from engine.pose.side import BodySide, side_landmarks
from engine.pose.types import Landmark
from engine.squat.features import extract_squat_features


def landmark(
    x: float = 0.0,
    y: float = 0.0,
    visibility: float = 1.0,
) -> Landmark:
    return Landmark(x=x, y=y, z=0.0, visibility=visibility)


def make_frame(
    side: BodySide = BodySide.LEFT,
    knee_visibility: float = 1.0,
):
    frame = [landmark(visibility=0.0) for _ in range(33)]
    indices = side_landmarks(side)

    frame[indices["shoulder"].value] = landmark(0.40, 0.20)
    frame[indices["hip"].value] = landmark(0.50, 0.50)
    frame[indices["knee"].value] = landmark(
        0.50,
        0.70,
        visibility=knee_visibility,
    )
    frame[indices["ankle"].value] = landmark(0.50, 0.90)
    frame[indices["heel"].value] = landmark(0.45, 0.95)
    frame[indices["toe"].value] = landmark(0.60, 0.95)
    return frame


def test_side_landmarks_uses_correct_right_knee():
    assert side_landmarks(BodySide.RIGHT)["knee"] == PoseLandmark.RIGHT_KNEE
    assert side_landmarks(BodySide.RIGHT)["knee"].value == 26


def test_extract_squat_features_preserves_frame_count_and_values():
    features = extract_squat_features(
        [make_frame(), make_frame()],
        side=BodySide.LEFT,
        image_size=(1000, 1000),
    )

    assert features.frame_count == 2
    assert features.hip_y_values == [0.50, 0.50]
    assert features.knee_angles == pytest.approx([0.0, 0.0])
    assert features.foot_lengths == pytest.approx([0.15, 0.15])
    assert features.valid_ratio("knee_angle") == 1.0


def test_extract_squat_features_keeps_invalid_frame_as_none():
    features = extract_squat_features(
        [
            make_frame(),
            make_frame(knee_visibility=0.2),
        ],
        side=BodySide.LEFT,
        image_size=(1000, 1000),
        visibility_threshold=0.5,
    )

    assert features.frame_count == 2
    assert features.knee_landmarks[1] is None
    assert features.knee_angles[1] is None
    assert features.hip_angles[1] is None
    assert features.valid_masks["knee_angle"] == [True, False]
    assert features.valid_ratio("knee_angle") == pytest.approx(0.5)


def test_extract_squat_features_uses_requested_side():
    left_frame = make_frame(BodySide.LEFT)
    right_indices = side_landmarks(BodySide.RIGHT)
    left_frame[right_indices["hip"].value] = landmark(0.60, 0.80)

    features = extract_squat_features(
        [left_frame],
        side=BodySide.RIGHT,
        image_size=(1000, 1000),
    )

    assert features.hip_y_values == [0.80]
    assert features.torso_angles == [None]


def test_extract_squat_features_rejects_invalid_visibility_threshold():
    with pytest.raises(ValueError, match="between 0 and 1"):
        extract_squat_features(
            [make_frame()],
            side=BodySide.LEFT,
            image_size=(1000, 1000),
            visibility_threshold=1.1,
        )


def test_squat_features_rejects_unknown_valid_ratio_name():
    features = extract_squat_features(
        [make_frame()],
        side=BodySide.LEFT,
        image_size=(1000, 1000),
    )

    with pytest.raises(ValueError, match="unsupported feature_name"):
        features.valid_ratio("unknown")


@pytest.mark.parametrize("image_size", [(1920, 1080), (1080, 1920), (1000, 1000)])
def test_geometry_uses_common_units_for_both_axes(image_size):
    width, height = image_size
    frame = make_frame()
    points = {
        "shoulder": (200, 200),
        "hip": (400, 400),
        "knee": (600, 400),
        "ankle": (600, 600),
        "heel": (550, 650),
        "toe": (750, 750),
    }
    indices = side_landmarks(BodySide.LEFT)
    for name, (x, y) in points.items():
        frame[indices[name]] = landmark(x / width, y / height)

    features = extract_squat_features(
        [frame], BodySide.LEFT, image_size=image_size,
    )

    assert features.torso_angles == pytest.approx([45.0])
    assert features.knee_angles == pytest.approx([90.0])
    assert features.hip_angles == pytest.approx([45.0])
    assert features.foot_lengths == pytest.approx([(200**2 + 100**2)**0.5 / width])
    assert features.hip_y_values == [400 / height]
    assert features.heel_y_values == [650 / height]
    assert features.knee_landmarks[0] is frame[indices["knee"]]
    assert features.toe_landmarks[0] is frame[indices["toe"]]


def test_extended_joints_have_zero_flexion():
    frame = make_frame()
    frame[PoseLandmark.LEFT_SHOULDER] = landmark(0.50, 0.20)
    features = extract_squat_features(
        [frame], BodySide.LEFT, image_size=(1920, 1080),
    )
    assert features.knee_angles == pytest.approx([0.0])
    assert features.hip_angles == pytest.approx([0.0])


@pytest.mark.parametrize("image_size", [(0, 1080), (1920, -1), (1.5, 2), (True, 2), (1,)])
def test_extract_squat_features_rejects_invalid_image_size(image_size):
    with pytest.raises(ValueError, match="positive integer width and height"):
        extract_squat_features([], BodySide.LEFT, image_size=image_size)


def test_extract_squat_features_requires_image_size():
    with pytest.raises(TypeError, match="image_size"):
        extract_squat_features([], BodySide.LEFT)


def test_degenerate_geometry_remains_invalid_after_scaling():
    frame = make_frame()
    frame[PoseLandmark.LEFT_SHOULDER] = frame[PoseLandmark.LEFT_HIP]
    frame[PoseLandmark.LEFT_ANKLE] = frame[PoseLandmark.LEFT_KNEE]
    frame[PoseLandmark.LEFT_FOOT_INDEX] = frame[PoseLandmark.LEFT_HEEL]
    features = extract_squat_features(
        [frame], BodySide.LEFT, image_size=(1920, 1080),
    )
    assert features.torso_angles == [None]
    assert features.knee_angles == [None]
    assert features.hip_angles == [None]
    assert features.foot_lengths == [None]
    assert features.valid_masks["knee_angle"] == [False]
