import pytest

from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide, side_landmarks
from engine.pose.types import Landmark
from engine.squat.features import extract_squat_features
from engine.squat.metrics import (
    KneeTravelNormalizationUnavailable,
    KneeTravelRecordingConditions,
    calculate_normalized_knee_travel,
)
from engine.squat.reps import SquatRep


CONFIRMED_CONDITIONS = KneeTravelRecordingConditions(side_view=True, foot_side_on=True)


def make_features(scale=1.0, image_size=(1920, 1080), direction=FacingDirection.RIGHT):
    width, height = image_size
    sign = 1 if direction == FacingDirection.RIGHT else -1
    frames = []
    indices = side_landmarks(BodySide.LEFT)
    for travel in (-20, 30, 50):
        frame = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(33)]
        for name, (x, y) in {
            "knee": (sign * travel, -100),
            "toe": (0, 0),
            "heel": (-sign * 100, 0),
        }.items():
            frame[indices[name]] = Landmark(
                0.5 + x * scale / width, 0.5 + y * scale / height, 0.0, 1.0,
            )
        frames.append(frame)
    return extract_squat_features(frames, BodySide.LEFT, image_size=image_size)


@pytest.mark.parametrize("direction", [FacingDirection.LEFT, FacingDirection.RIGHT])
@pytest.mark.parametrize("scale", [0.5, 1.0, 2.0])
@pytest.mark.parametrize("image_size", [(1920, 1080), (1080, 1920)])
def test_normalized_travel_is_invariant_to_subject_scale_and_image_size(direction, scale, image_size):
    result = calculate_normalized_knee_travel(
        make_features(scale, image_size, direction), SquatRep(0, 1, 2), direction,
        recording_conditions=CONFIRMED_CONDITIONS,
    )
    assert result.normalized_travel == pytest.approx(0.5)
    assert result.raw_result.max_travel == pytest.approx(50 * scale / image_size[0])
    assert result.raw_result.max_travel_index == 2
    assert result.reference_frame_count == 3


def test_reference_is_rep_local_median_not_peak_frame_length():
    features = make_features()
    features.foot_lengths = [1000 / 1920, 100 / 1920, 300 / 1920]
    result = calculate_normalized_knee_travel(
        features, SquatRep(1, 1, 2), FacingDirection.RIGHT,
        recording_conditions=CONFIRMED_CONDITIONS,
    )
    assert result.reference_foot_length == pytest.approx(200 / 1920)
    assert result.normalized_travel == pytest.approx(0.25)
    assert result.reference_frame_count == 2


def test_missing_peak_heel_uses_other_rep_frames_without_shifting_peak():
    features = make_features()
    features.foot_lengths[2] = None
    features.valid_masks["foot_length"][2] = False
    result = calculate_normalized_knee_travel(
        features, SquatRep(0, 1, 2), FacingDirection.RIGHT,
        recording_conditions=CONFIRMED_CONDITIONS,
    )
    assert result.normalized_travel == pytest.approx(0.5)
    assert result.raw_result.max_travel_index == 2
    assert result.reference_frame_count == 2


def test_reference_ignores_masked_outlier():
    features = make_features()
    features.foot_lengths[1] = 10.0
    features.valid_masks["foot_length"][1] = False
    result = calculate_normalized_knee_travel(
        features, SquatRep(0, 1, 2), FacingDirection.RIGHT,
        recording_conditions=CONFIRMED_CONDITIONS,
    )
    assert result.normalized_travel == pytest.approx(0.5)


@pytest.mark.parametrize("length", [None, 0.0, -1.0, float("nan"), float("inf")])
def test_normalization_rejects_rep_without_usable_reference(length):
    features = make_features()
    features.foot_lengths[1:] = [length, length]
    with pytest.raises(ValueError, match="no valid positive foot lengths"):
        calculate_normalized_knee_travel(
            features, SquatRep(1, 1, 2), FacingDirection.RIGHT,
            recording_conditions=CONFIRMED_CONDITIONS,
        )


@pytest.mark.parametrize("field", ["foot_lengths", "mask"])
def test_normalization_rejects_misaligned_reference(field):
    features = make_features()
    values = features.foot_lengths if field == "foot_lengths" else features.valid_masks["foot_length"]
    values.pop()
    with pytest.raises(ValueError, match="must have the same length"):
        calculate_normalized_knee_travel(
            features, SquatRep(0, 1, 2), FacingDirection.RIGHT,
            recording_conditions=CONFIRMED_CONDITIONS,
        )


def test_normalization_preserves_negative_travel():
    result = calculate_normalized_knee_travel(
        make_features(), SquatRep(0, 0, 0), FacingDirection.RIGHT,
        recording_conditions=CONFIRMED_CONDITIONS,
    )
    assert result.normalized_travel == pytest.approx(-0.2)


@pytest.mark.parametrize(
    ("conditions", "reason"),
    [
        (None, "side_view_unverified"),
        (KneeTravelRecordingConditions(), "side_view_unverified"),
        (KneeTravelRecordingConditions(side_view=False, foot_side_on=True), "not_side_view"),
        (KneeTravelRecordingConditions(side_view=True), "foot_orientation_unverified"),
        (KneeTravelRecordingConditions(side_view=True, foot_side_on=False), "foot_not_side_on"),
        (KneeTravelRecordingConditions(side_view=1, foot_side_on=True), "side_view_unverified"),
        (KneeTravelRecordingConditions(side_view=True, foot_side_on="yes"), "foot_orientation_unverified"),
    ],
)
def test_unverified_or_unsuitable_recording_never_produces_normalized_value(conditions, reason):
    with pytest.raises(KneeTravelNormalizationUnavailable) as error:
        calculate_normalized_knee_travel(
            make_features(), SquatRep(0, 1, 2), FacingDirection.RIGHT,
            recording_conditions=conditions,
        )
    assert error.value.reason == reason
    assert error.value.raw_result.max_travel_index == 2
    assert error.value.raw_result.max_travel == pytest.approx(50 / 1920)


def test_recording_check_does_not_change_raw_metric_availability():
    from engine.squat.metrics import calculate_knee_travel_from_features

    result = calculate_knee_travel_from_features(
        make_features(), SquatRep(0, 1, 2), FacingDirection.RIGHT,
    )
    assert result.max_travel_index == 2
