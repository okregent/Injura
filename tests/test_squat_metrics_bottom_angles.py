import pytest

from engine.pose.side import BodySide, side_landmarks
from engine.pose.types import Landmark
from engine.squat.features import extract_squat_features
from engine.squat.metrics import calculate_bottom_joint_angles
from engine.squat.reps import SquatRep


def make_features():
    indices = side_landmarks(BodySide.LEFT)
    frames = []
    for hip_y in (0.5, 0.7, 0.6):
        frame = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(33)]
        for name, (x, y) in {
            "shoulder": (0.4, hip_y - 0.1),
            "hip": (0.5, hip_y),
            "knee": (0.6, hip_y),
            "ankle": (0.6, hip_y + 0.2),
        }.items():
            frame[indices[name]] = Landmark(x, y, 0.0, 1.0)
        frames.append(frame)
    return extract_squat_features(frames, BodySide.LEFT, image_size=(1000, 1000))


def test_bottom_angles_use_deepest_hip_not_last_bottom_phase_frame():
    result = calculate_bottom_joint_angles(make_features(), SquatRep(0, 2, 2))
    assert result.deepest_index == 1
    assert result.deepest_hip_y == pytest.approx(0.7)
    assert result.knee_flexion_angle == pytest.approx(90)
    assert result.hip_flexion_angle == pytest.approx(45)


def test_bottom_search_is_rep_local_and_preserves_first_tie():
    features = make_features()
    features.hip_y_values = [0.9, 0.7, 0.7]
    result = calculate_bottom_joint_angles(features, SquatRep(1, 2, 2))
    assert result.deepest_index == 1


@pytest.mark.parametrize("field,mask", [("knee_angles", "knee_angle"), ("hip_angles", "hip_angle")])
@pytest.mark.parametrize("mode", ["missing", "masked", "nonfinite"])
def test_missing_angle_is_independent_and_does_not_shift_bottom(field, mask, mode):
    features = make_features()
    if mode == "missing":
        getattr(features, field)[1] = None
    elif mode == "masked":
        features.valid_masks[mask][1] = False
    else:
        getattr(features, field)[1] = float("nan")
    result = calculate_bottom_joint_angles(features, SquatRep(0, 2, 2))
    assert result.deepest_index == 1
    if field == "knee_angles":
        assert result.knee_flexion_angle is None
        assert result.hip_flexion_angle == pytest.approx(45)
    else:
        assert result.hip_flexion_angle is None
        assert result.knee_flexion_angle == pytest.approx(90)


def test_missing_both_angles_returns_none_instead_of_borrowing_neighbor():
    features = make_features()
    features.knee_angles[1] = features.hip_angles[1] = None
    result = calculate_bottom_joint_angles(features, SquatRep(0, 2, 2))
    assert result.deepest_index == 1
    assert result.knee_flexion_angle is result.hip_flexion_angle is None


def test_bottom_uses_only_finite_unmasked_hip_observations():
    features = make_features()
    features.hip_y_values[0] = float("nan")
    features.valid_masks["hip_y"][1] = False
    result = calculate_bottom_joint_angles(features, SquatRep(0, 2, 2))
    assert result.deepest_index == 2


def test_no_valid_hip_observation_raises():
    features = make_features()
    features.hip_y_values = [None] * 3
    with pytest.raises(ValueError, match="no valid hip y-values"):
        calculate_bottom_joint_angles(features, SquatRep(0, 2, 2))


@pytest.mark.parametrize("rep", [SquatRep(-1, 1, 2), SquatRep(2, 1, 0), SquatRep(0, 1, 3)])
def test_invalid_rep_range_raises(rep):
    with pytest.raises(ValueError, match="inclusive range"):
        calculate_bottom_joint_angles(make_features(), rep)


@pytest.mark.parametrize("field", ["knee_angles", "hip_angles", "hip_y_mask"])
def test_misaligned_features_raise(field):
    features = make_features()
    values = features.valid_masks["hip_y"] if field == "hip_y_mask" else getattr(features, field)
    values.pop()
    with pytest.raises(ValueError, match="same length"):
        calculate_bottom_joint_angles(features, SquatRep(0, 2, 2))
