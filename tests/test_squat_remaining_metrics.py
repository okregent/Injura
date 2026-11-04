import math

import pytest

from engine.analyzer import ExerciseAnalyzer
from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide, side_landmarks
from engine.pose.types import Landmark, PoseExtractionResult
from engine.squat.analyzer import SquatAnalyzer
from engine.squat.features import extract_squat_features
from engine.squat.metrics import (
    KneeTravelRecordingConditions, calculate_consistency, calculate_heel_lift,
    calculate_hip_to_knee_depth, calculate_rep_timing,
)
from engine.squat.phases import SquatPhase
from engine.squat.reps import SquatRep


def sample_extraction(two_reps=False, fps=10.0):
    hip_values = [0.3, 0.3, 0.4, 0.5, 0.6, 0.7, 0.7, 0.6, 0.5, 0.4, 0.3]
    if two_reps:
        hip_values += hip_values[1:]
    frames = []
    indices = side_landmarks(BodySide.LEFT)
    for hip_y in hip_values:
        frame = [Landmark(0.0, 0.0, 0.0, 0.0) for _ in range(33)]
        for name, (x, y) in {
            "shoulder": (0.45, hip_y - 0.2), "hip": (0.5, hip_y),
            "knee": (0.6 + 0.15 * (hip_y - 0.3) / 0.4, 0.65),
            "ankle": (0.6, 0.8), "heel": (0.5, 0.78 if hip_y > 0.65 else 0.8),
            "toe": (0.7, 0.8),
        }.items():
            frame[indices[name]] = Landmark(x, y, 0.0, 1.0)
        frames.append(frame)
    return PoseExtractionResult(frames, list(range(len(frames))), len(frames), (1920, 1080), fps)


def sample_features(extraction=None):
    extraction = extraction or sample_extraction()
    return extract_squat_features(extraction.pose_sequence, BodySide.LEFT, image_size=extraction.image_size)


def analyze(extraction=None, **kwargs):
    return SquatAnalyzer().analyze(
        extraction or sample_extraction(), side=BodySide.LEFT,
        facing_direction=FacingDirection.RIGHT, **kwargs,
    )


def test_hip_to_knee_depth_is_signed_same_frame_separation():
    features = sample_features()
    result = calculate_hip_to_knee_depth(features, SquatRep(2, 6, 10))
    assert result.deepest_index == 5
    assert result.vertical_gap == pytest.approx(0.05)
    result = calculate_hip_to_knee_depth(features, SquatRep(2, 3, 4))
    assert result.vertical_gap == pytest.approx(-0.05)


def test_missing_bottom_knee_does_not_borrow_neighbor():
    features = sample_features()
    features.knee_landmarks[5] = None
    with pytest.raises(ValueError, match="knee is unavailable"):
        calculate_hip_to_knee_depth(features, SquatRep(2, 6, 10))


def test_heel_rise_magnitude_and_observed_duration():
    extraction = sample_extraction()
    result = calculate_heel_lift(sample_features(extraction), SquatRep(2, 6, 10), extraction)
    assert result.max_lift == pytest.approx(0.02)
    assert result.max_lift_index == 5
    assert result.lifted_seconds == pytest.approx(0.2)
    assert result.timed_coverage == 1.0


def test_heel_proxy_cancels_shared_vertical_translation():
    features = sample_features()
    for index, toe in enumerate(features.toe_landmarks):
        shift = index * 0.01
        toe.y += shift
        features.heel_y_values[index] += shift
    result = calculate_heel_lift(features, SquatRep(2, 6, 10))
    assert result.max_lift == pytest.approx(0.02)
    assert result.lifted_seconds is None


def test_heel_missing_baseline_is_unavailable():
    features = sample_features()
    features.heel_y_values[2] = None
    with pytest.raises(ValueError, match="baseline"):
        calculate_heel_lift(features, SquatRep(2, 6, 10))


def test_heel_duration_excludes_missing_and_unobserved_intervals():
    extraction = sample_extraction()
    features = sample_features(extraction)
    features.heel_y_values[6] = None
    result = calculate_heel_lift(features, SquatRep(2, 6, 10), extraction)
    assert result.lifted_seconds == 0.0
    assert result.timed_coverage == pytest.approx(6 / 8)
    extraction.source_frame_indices = [index if index < 6 else index + 4 for index in range(11)]
    extraction.source_frame_count = 15
    result = calculate_heel_lift(sample_features(extraction), SquatRep(2, 6, 10), extraction)
    assert result.lifted_seconds == pytest.approx(0.1)
    assert result.timed_coverage == pytest.approx(7 / 12)


def test_timing_sums_half_open_phase_intervals_without_extra_endpoint_frame():
    result = analyze()
    extraction = sample_extraction()
    timing = calculate_rep_timing(extraction, result.phases, result.repetitions[0].rep)
    assert timing.descent_seconds == pytest.approx(0.3)
    assert timing.bottom_seconds == pytest.approx(0.2)
    assert timing.ascent_seconds == pytest.approx(0.3)
    assert timing.total_seconds == pytest.approx(0.8)
    assert timing.total_seconds == pytest.approx(
        timing.descent_seconds + timing.bottom_seconds + timing.ascent_seconds,
    )
    assert timing.start_source_frame == 2
    assert timing.end_source_frame == 10


def test_timing_rejects_source_frame_gaps():
    extraction = sample_extraction()
    phases = analyze(extraction).phases
    extraction.source_frame_indices = [index if index < 6 else index + 2 for index in range(11)]
    extraction.source_frame_count = 13
    with pytest.raises(ValueError, match="missing source frames"):
        calculate_rep_timing(extraction, phases, SquatRep(2, 6, 10))


def test_timing_rejects_unknown_or_reordered_phase():
    extraction = sample_extraction()
    phases = analyze(extraction).phases
    phases[4] = SquatPhase.UNKNOWN
    with pytest.raises(ValueError, match="ordered descent"):
        calculate_rep_timing(extraction, phases, SquatRep(2, 6, 10))


def test_consistency_requires_two_finite_reps_and_retains_units():
    result = calculate_consistency([1.0, 3.0, None, math.nan])
    assert result.valid_count == 2
    assert result.total_count == 4
    assert result.mean == 2.0
    assert result.standard_deviation == 1.0
    assert result.value_range == 2.0
    assert calculate_consistency([2.0]).standard_deviation is None
    assert calculate_consistency([]).mean is None
    assert calculate_consistency([-1.0, 1.0]).standard_deviation == 1.0


def test_analyzer_integrates_two_complete_reps_and_consistency():
    assert isinstance(SquatAnalyzer(), ExerciseAnalyzer)
    result = analyze(
        sample_extraction(two_reps=True),
        recording_conditions=KneeTravelRecordingConditions(True, True),
    )
    assert len(result.repetitions) == 2
    for rep in result.repetitions:
        assert len(rep.metrics) == 9
        assert all(outcome.value is not None for outcome in rep.metrics.values())
        assert all(outcome.quality.status == "available" for outcome in rep.metrics.values())
    assert result.consistency["depth"].valid_count == 2
    assert result.consistency["depth"].standard_deviation == pytest.approx(0)
    assert result.consistency["timing"].standard_deviation == pytest.approx(0)


def test_unverified_recording_excludes_only_normalization():
    metrics = analyze().repetitions[0].metrics
    assert metrics["normalized_knee_travel"].value is None
    assert "side_view_unverified" in metrics["normalized_knee_travel"].quality.reason
    assert metrics["knee_travel"].value is not None
    assert metrics["hip_to_knee"].value is not None


def test_missing_fps_excludes_timing_without_losing_other_metrics():
    metrics = analyze(sample_extraction(fps=None)).repetitions[0].metrics
    assert metrics["timing"].quality.status == "unavailable"
    assert metrics["heel_lift"].value.lifted_seconds is None
    assert metrics["depth"].value is not None


def test_missing_source_frame_splits_detection_instead_of_inventing_rep():
    extraction = sample_extraction(two_reps=True)
    extraction.source_frame_indices = [index if index < 5 else index + 1 for index in range(21)]
    extraction.source_frame_count = 22
    result = analyze(extraction)
    assert len(result.repetitions) == 1
    assert result.repetitions[0].rep.start_index > 5
    assert result.issues


def test_missing_hip_splits_detection_and_retains_frame_alignment():
    extraction = sample_extraction(two_reps=True)
    extraction.pose_sequence[4][side_landmarks(BodySide.LEFT)["hip"]].visibility = 0
    result = analyze(extraction)
    assert result.features.frame_count == 21
    assert result.phases[4] == SquatPhase.UNKNOWN
    assert len(result.repetitions) == 1


def test_missing_shoulder_baseline_isolated_and_coverage_reported():
    extraction = sample_extraction()
    extraction.pose_sequence[2][side_landmarks(BodySide.LEFT)["shoulder"]].visibility = 0
    metrics = analyze(extraction).repetitions[0].metrics
    assert metrics["torso_lean"].value is None
    assert metrics["torso_lean"].quality.coverage == pytest.approx(8 / 9)
    assert metrics["hip_flexion"].value is not None


def test_empty_and_stationary_sequences_return_explicit_issue():
    assert not analyze(PoseExtractionResult([], [], 0, (1920, 1080), 30)).repetitions
    extraction = sample_extraction()
    hip = side_landmarks(BodySide.LEFT)["hip"]
    for frame in extraction.pose_sequence:
        frame[hip].y = 0.5
    assert not analyze(extraction).repetitions


@pytest.mark.parametrize("fps", [0, -1, math.nan, math.inf, True])
def test_invalid_fps_is_rejected(fps):
    with pytest.raises(ValueError, match="fps must be finite and positive"):
        sample_extraction(fps=fps)
