import pytest
import math

from engine.pose.landmarks import PoseLandmark
from engine.pose.side import BodySide
from engine.pose.types import Landmark
from engine.squat.features import extract_squat_features
from engine.squat.metrics.torso_lean import (
    calculate_torso_lean,
    calculate_torso_lean_from_features,
)
from engine.squat.reps import SquatRep


def make_rep(
    start_index: int = 1,
    bottom_index: int = 3,
    end_index: int = 5,
) -> SquatRep:
    return SquatRep(
        start_index=start_index,
        bottom_index=bottom_index,
        end_index=end_index,
    )


def make_torso_features(angles, invalid_indices=()):
    frames = []
    width, height = 1920, 1080
    for index, angle in enumerate(angles):
        frame = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(33)]
        radians = math.radians(angle)
        frame[PoseLandmark.LEFT_HIP] = Landmark(0.5, 0.7, 0.0, 1.0)
        frame[PoseLandmark.LEFT_SHOULDER] = Landmark(
            0.5 + 200 * math.sin(radians) / width,
            0.7 - 200 * math.cos(radians) / height,
            0.0,
            0.1 if index in invalid_indices else 1.0,
        )
        frames.append(frame)
    return extract_squat_features(
        frames, BodySide.LEFT, image_size=(width, height),
    )


def test_torso_lean_from_features_matches_existing_calculation():
    angles = [5, 10, 18, 32, 25, 12]
    result = calculate_torso_lean_from_features(make_torso_features(angles), make_rep())
    expected = calculate_torso_lean(angles, make_rep())
    assert result.max_lean_angle == pytest.approx(expected.max_lean_angle)
    assert result.max_lean_index == expected.max_lean_index
    assert result.standing_angle == pytest.approx(expected.standing_angle)
    assert result.lean_change == pytest.approx(expected.lean_change)


def test_torso_lean_from_features_skips_missing_frames_and_keeps_indices():
    features = make_torso_features([70, 10, 60, 32, 25, 12, 80], invalid_indices=(2,))
    result = calculate_torso_lean_from_features(features, make_rep())
    assert result.max_lean_index == 3
    assert result.max_lean_angle == pytest.approx(32)
    assert result.standing_angle == pytest.approx(10)
    assert result.lean_change == pytest.approx(22)


def test_torso_lean_from_features_honors_numeric_frame_mask():
    features = make_torso_features([5, 10, 60, 32, 25, 12])
    features.valid_masks["torso_angle"][2] = False
    result = calculate_torso_lean_from_features(features, make_rep())
    assert result.max_lean_index == 3


@pytest.mark.parametrize("masked_only", [False, True])
def test_torso_lean_rejects_missing_rep_start_instead_of_shifting_baseline(masked_only):
    features = make_torso_features(
        [5, 10, 18, 32, 25, 12], invalid_indices=() if masked_only else (1,),
    )
    features.valid_masks["torso_angle"][1] = False
    with pytest.raises(ValueError, match="rep start must have a valid torso angle"):
        calculate_torso_lean_from_features(features, make_rep())


def test_torso_lean_rejects_rep_without_valid_angles():
    features = make_torso_features([5, 10, 18], invalid_indices=(1, 2))
    with pytest.raises(ValueError, match="rep contains no valid torso angles"):
        calculate_torso_lean_from_features(
            features, make_rep(start_index=1, end_index=2),
        )


def test_torso_lean_rejects_misaligned_mask():
    features = make_torso_features([5, 10, 18, 32, 25, 12])
    features.valid_masks["torso_angle"].pop()
    with pytest.raises(ValueError, match="must have the same length"):
        calculate_torso_lean_from_features(features, make_rep())


def test_calculate_torso_lean_returns_expected_result():
    torso_angles = [
        5,
        10,
        18,
        32,
        25,
        12,
    ]

    result = calculate_torso_lean(
        torso_angles,
        make_rep(),
    )

    assert result.max_lean_angle == pytest.approx(32)
    assert result.max_lean_index == 3
    assert result.standing_angle == pytest.approx(10)
    assert result.lean_change == pytest.approx(22)


def test_calculate_torso_lean_only_searches_inside_rep():
    torso_angles = [
        60,
        10,
        18,
        32,
        25,
        12,
        70,
    ]

    result = calculate_torso_lean(
        torso_angles,
        make_rep(start_index=1, end_index=5),
    )

    assert result.max_lean_index == 3
    assert result.max_lean_angle == pytest.approx(32)


def test_calculate_torso_lean_uses_first_maximum():
    torso_angles = [
        5,
        10,
        30,
        30,
        25,
        12,
    ]

    result = calculate_torso_lean(
        torso_angles,
        make_rep(),
    )

    assert result.max_lean_index == 2


def test_calculate_torso_lean_returns_zero_change():
    torso_angles = [
        5,
        20,
        18,
        15,
        12,
        10,
    ]

    result = calculate_torso_lean(
        torso_angles,
        make_rep(),
    )

    assert result.max_lean_angle == 20
    assert result.lean_change == 0


def test_calculate_torso_lean_raises_for_empty_input():
    with pytest.raises(
        ValueError,
        match="torso_angles list cannot be empty",
    ):
        calculate_torso_lean([], make_rep())


def test_calculate_torso_lean_raises_for_negative_start():
    with pytest.raises(
        ValueError,
        match="rep.start_index cannot be negative",
    ):
        calculate_torso_lean(
            [1, 2, 3],
            make_rep(start_index=-1, end_index=2),
        )


def test_calculate_torso_lean_raises_when_start_after_end():
    with pytest.raises(
        ValueError,
        match="rep.start_index must not be greater than rep.end_index",
    ):
        calculate_torso_lean(
            [1, 2, 3],
            make_rep(start_index=2, end_index=1),
        )


def test_calculate_torso_lean_raises_when_end_out_of_range():
    with pytest.raises(
        ValueError,
        match="rep.end_index is outside torso_angles range",
    ):
        calculate_torso_lean(
            [1, 2, 3],
            make_rep(start_index=0, end_index=3),
        )
