import pytest

from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide, side_landmarks
from engine.pose.types import Landmark
from engine.squat.features import extract_squat_features
from engine.squat.metrics.knee_travel import (
    calculate_knee_travel,
    calculate_knee_travel_from_features,
)
from engine.squat.reps import SquatRep


def make_landmark(x: float) -> Landmark:
    return Landmark(
        x=x,
        y=0.0,
        z=0.0,
        visibility=1.0,
    )


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


def make_knee_features(knee_x, toe_x, side=BodySide.LEFT, invalid_knees=(), invalid_toes=()):
    frames = []
    indices = side_landmarks(side)
    for index, (knee, toe) in enumerate(zip(knee_x, toe_x)):
        frame = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(33)]
        frame[indices["knee"]] = Landmark(
            knee, 0.6, 0.0, 0.1 if index in invalid_knees else 1.0,
        )
        frame[indices["toe"]] = Landmark(
            toe, 0.9, 0.0, 0.1 if index in invalid_toes else 1.0,
        )
        frames.append(frame)
    return extract_squat_features(frames, side, image_size=(1920, 1080))


@pytest.mark.parametrize("side", [BodySide.LEFT, BodySide.RIGHT])
@pytest.mark.parametrize("direction", [FacingDirection.LEFT, FacingDirection.RIGHT])
def test_knee_travel_from_features_keeps_body_side_independent_of_direction(side, direction):
    knee_x = [0.4, 0.5, 0.58, 0.7, 0.63, 0.54]
    toe_x = [0.5, 0.55, 0.56, 0.6, 0.59, 0.55]
    features = make_knee_features(knee_x, toe_x, side)
    assert calculate_knee_travel_from_features(features, make_rep(), direction) == (
        calculate_knee_travel(
            [make_landmark(x) for x in knee_x],
            [make_landmark(x) for x in toe_x], make_rep(), direction,
        )
    )


def test_knee_travel_skips_either_missing_landmark_without_compacting_indices():
    features = make_knee_features(
        [0.99, 0.9, 0.8, 0.7, 0.6, 0.99], [0.5] * 6,
        invalid_knees=(1,), invalid_toes=(2,),
    )
    result = calculate_knee_travel_from_features(
        features, make_rep(start_index=1, end_index=4), FacingDirection.RIGHT,
    )
    assert result.max_travel_index == 3
    assert result.max_travel == pytest.approx(0.2)


@pytest.mark.parametrize("mask_name", ["knee", "toe"])
def test_knee_travel_honors_each_numeric_landmark_mask(mask_name):
    features = make_knee_features([0.5, 0.9, 0.7], [0.5] * 3)
    features.valid_masks[mask_name][1] = False
    result = calculate_knee_travel_from_features(
        features, make_rep(start_index=0, end_index=2), FacingDirection.RIGHT,
    )
    assert result.max_travel_index == 2


def test_knee_travel_requires_valid_landmarks_in_the_same_frame():
    features = make_knee_features(
        [0.7, 0.8, 0.9], [0.5] * 3, invalid_knees=(1,), invalid_toes=(2,),
    )
    with pytest.raises(ValueError, match="no valid knee/toe pairs"):
        calculate_knee_travel_from_features(
            features, make_rep(start_index=1, end_index=2), FacingDirection.RIGHT,
        )


@pytest.mark.parametrize("mask_name", ["knee", "toe"])
def test_knee_travel_rejects_misaligned_feature_masks(mask_name):
    features = make_knee_features([0.5, 0.6, 0.7], [0.5] * 3)
    features.valid_masks[mask_name].pop()
    with pytest.raises(ValueError, match="must have the same length"):
        calculate_knee_travel_from_features(
            features, make_rep(start_index=0, end_index=2), FacingDirection.RIGHT,
        )


def test_knee_travel_from_features_retains_negative_travel():
    features = make_knee_features([0.4, 0.45, 0.47], [0.5] * 3)
    result = calculate_knee_travel_from_features(
        features, make_rep(start_index=0, end_index=2), FacingDirection.RIGHT,
    )
    assert result.max_travel == pytest.approx(-0.03)


def test_knee_travel_rejects_invalid_direction():
    with pytest.raises(ValueError, match="unsupported facing_direction"):
        calculate_knee_travel(
            [make_landmark(0.7)], [make_landmark(0.5)],
            make_rep(start_index=0, end_index=0), "right",
        )


def test_calculate_knee_travel_facing_right():
    knee_landmarks = [
        make_landmark(0.40),
        make_landmark(0.50),
        make_landmark(0.58),
        make_landmark(0.70),
        make_landmark(0.63),
        make_landmark(0.54),
    ]

    toe_landmarks = [
        make_landmark(0.50),
        make_landmark(0.55),
        make_landmark(0.56),
        make_landmark(0.60),
        make_landmark(0.59),
        make_landmark(0.55),
    ]

    result = calculate_knee_travel(
        knee_landmarks=knee_landmarks,
        toe_landmarks=toe_landmarks,
        rep=make_rep(),
        facing_direction=FacingDirection.RIGHT,
    )

    assert result.max_travel == pytest.approx(0.10)
    assert result.max_travel_index == 3
    assert result.knee_x == pytest.approx(0.70)
    assert result.toe_x == pytest.approx(0.60)


def test_calculate_knee_travel_facing_left():
    knee_landmarks = [
        make_landmark(0.60),
        make_landmark(0.50),
        make_landmark(0.42),
        make_landmark(0.30),
        make_landmark(0.37),
        make_landmark(0.46),
    ]

    toe_landmarks = [
        make_landmark(0.50),
        make_landmark(0.45),
        make_landmark(0.44),
        make_landmark(0.40),
        make_landmark(0.41),
        make_landmark(0.45),
    ]

    result = calculate_knee_travel(
        knee_landmarks=knee_landmarks,
        toe_landmarks=toe_landmarks,
        rep=make_rep(),
        facing_direction=FacingDirection.LEFT,
    )

    assert result.max_travel == pytest.approx(0.10)
    assert result.max_travel_index == 3
    assert result.knee_x == pytest.approx(0.30)
    assert result.toe_x == pytest.approx(0.40)


def test_calculate_knee_travel_can_return_negative_value():
    knee_landmarks = [
        make_landmark(0.40),
        make_landmark(0.45),
        make_landmark(0.47),
    ]

    toe_landmarks = [
        make_landmark(0.50),
        make_landmark(0.50),
        make_landmark(0.50),
    ]

    result = calculate_knee_travel(
        knee_landmarks=knee_landmarks,
        toe_landmarks=toe_landmarks,
        rep=make_rep(
            start_index=0,
            bottom_index=1,
            end_index=2,
        ),
        facing_direction=FacingDirection.RIGHT,
    )

    assert result.max_travel == pytest.approx(-0.03)
    assert result.max_travel_index == 2


def test_calculate_knee_travel_only_searches_inside_rep():
    knee_landmarks = [
        make_landmark(0.90),
        make_landmark(0.50),
        make_landmark(0.58),
        make_landmark(0.70),
        make_landmark(0.63),
        make_landmark(0.54),
        make_landmark(0.99),
    ]

    toe_landmarks = [
        make_landmark(0.50),
        make_landmark(0.55),
        make_landmark(0.56),
        make_landmark(0.60),
        make_landmark(0.59),
        make_landmark(0.55),
        make_landmark(0.50),
    ]

    result = calculate_knee_travel(
        knee_landmarks=knee_landmarks,
        toe_landmarks=toe_landmarks,
        rep=make_rep(start_index=1, end_index=5),
        facing_direction=FacingDirection.RIGHT,
    )

    assert result.max_travel_index == 3
    assert result.max_travel == pytest.approx(0.10)


def test_calculate_knee_travel_uses_first_maximum():
    knee_landmarks = [
        make_landmark(0.40),
        make_landmark(0.55),  # travel 0.05
        make_landmark(0.70),  # travel 0.10
        make_landmark(0.70),  # travel 0.10
        make_landmark(0.60),
        make_landmark(0.50),
    ]

    toe_landmarks = [
        make_landmark(0.50),
        make_landmark(0.50),
        make_landmark(0.60),
        make_landmark(0.60),
        make_landmark(0.55),
        make_landmark(0.50),
    ]

    result = calculate_knee_travel(
        knee_landmarks=knee_landmarks,
        toe_landmarks=toe_landmarks,
        rep=make_rep(),
        facing_direction=FacingDirection.RIGHT,
    )

    assert result.max_travel_index == 2
    assert result.max_travel == pytest.approx(0.10)

def test_calculate_knee_travel_raises_for_empty_knee_landmarks():
    with pytest.raises(
        ValueError,
        match="knee_landmarks list cannot be empty",
    ):
        calculate_knee_travel(
            knee_landmarks=[],
            toe_landmarks=[make_landmark(0.5)],
            rep=make_rep(start_index=0, end_index=0),
            facing_direction=FacingDirection.RIGHT,
        )


def test_calculate_knee_travel_raises_for_empty_toe_landmarks():
    with pytest.raises(
        ValueError,
        match="toe_landmarks list cannot be empty",
    ):
        calculate_knee_travel(
            knee_landmarks=[make_landmark(0.5)],
            toe_landmarks=[],
            rep=make_rep(start_index=0, end_index=0),
            facing_direction=FacingDirection.RIGHT,
        )


def test_calculate_knee_travel_raises_for_length_mismatch():
    with pytest.raises(
        ValueError,
        match="must have the same length",
    ):
        calculate_knee_travel(
            knee_landmarks=[
                make_landmark(0.5),
                make_landmark(0.6),
            ],
            toe_landmarks=[make_landmark(0.5)],
            rep=make_rep(start_index=0, end_index=0),
            facing_direction=FacingDirection.RIGHT,
        )


def test_calculate_knee_travel_raises_for_negative_start():
    with pytest.raises(
        ValueError,
        match="rep.start_index cannot be negative",
    ):
        calculate_knee_travel(
            knee_landmarks=[make_landmark(0.5)] * 3,
            toe_landmarks=[make_landmark(0.5)] * 3,
            rep=make_rep(start_index=-1, end_index=2),
            facing_direction=FacingDirection.RIGHT,
        )


def test_calculate_knee_travel_raises_when_start_after_end():
    with pytest.raises(
        ValueError,
        match="rep.start_index must not be greater than rep.end_index",
    ):
        calculate_knee_travel(
            knee_landmarks=[make_landmark(0.5)] * 3,
            toe_landmarks=[make_landmark(0.5)] * 3,
            rep=make_rep(start_index=2, end_index=1),
            facing_direction=FacingDirection.RIGHT,
        )


def test_calculate_knee_travel_raises_when_end_out_of_range():
    with pytest.raises(
        ValueError,
        match="rep.end_index is outside landmark range",
    ):
        calculate_knee_travel(
            knee_landmarks=[make_landmark(0.5)] * 3,
            toe_landmarks=[make_landmark(0.5)] * 3,
            rep=make_rep(start_index=0, end_index=3),
            facing_direction=FacingDirection.RIGHT,
        )
