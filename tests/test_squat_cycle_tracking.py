import pytest

from engine.pose.side import BodySide, side_landmarks
from engine.squat.cycles import detect_cycle_phases
from engine.squat.phases import SquatPhase, SquatPhaseThresholds
from engine.squat.reps import detect_squat_reps
from tests.test_squat_remaining_metrics import analyze, sample_extraction


THRESHOLDS = SquatPhaseThresholds(0.0, 1.0, 0.03)


def test_direction_jitter_does_not_split_descent_or_ascent():
    phases = detect_cycle_phases([0, .2, .4, .39, .6, .9, .86, .82, .74, .70, .71, .4, 0], THRESHOLDS)
    runs = [p for i, p in enumerate(phases) if i == 0 or phases[i - 1] != p]
    assert runs == [SquatPhase.STANDING, SquatPhase.DESCENDING, SquatPhase.BOTTOM,
                    SquatPhase.ASCENDING, SquatPhase.STANDING]
    assert len(detect_squat_reps(phases)) == 1


def test_bottom_hysteresis_prevents_threshold_chatter():
    phases = detect_cycle_phases([0, .2, .6, .86, .84, .87, .83, .76, .74, .7, .2, 0], THRESHOLDS)
    assert phases[3:8] == [SquatPhase.BOTTOM] * 5
    assert phases[8] == SquatPhase.ASCENDING


def test_initial_partial_rep_requires_observed_standing_before_new_rep():
    phases = detect_cycle_phases([.5, .9, .7, 0, .2, .9, .7, 0], THRESHOLDS)
    reps = detect_squat_reps(phases)
    assert len(reps) == 1
    assert reps[0].start_index == 4


def test_real_double_dip_is_not_hidden_by_monotonic_labels():
    phases = detect_cycle_phases([0, .2, .9, .7, .9, .7, 0], THRESHOLDS)
    assert phases[3:6] == [SquatPhase.ASCENDING, SquatPhase.BOTTOM, SquatPhase.ASCENDING]


def test_aborted_descent_is_cancelled_before_next_actual_rep():
    phases = [SquatPhase.STANDING, SquatPhase.DESCENDING, SquatPhase.STANDING,
              SquatPhase.STANDING, SquatPhase.DESCENDING, SquatPhase.BOTTOM,
              SquatPhase.ASCENDING, SquatPhase.STANDING]
    reps = detect_squat_reps(phases)
    assert len(reps) == 1
    assert reps[0].start_index == 4


def test_short_gap_returns_candidate_without_inventing_metric_values():
    extraction = sample_extraction()
    extraction.source_frame_indices = [i if i < 5 else i + 1 for i in range(11)]
    extraction.source_frame_count = 12
    result = analyze(extraction)
    assert result.repetitions == []
    assert len(result.candidates) == 1
    assert result.candidates[0].missing_source_frames == 1
    assert result.consistency["depth"].valid_count == 0
    assert result.features.frame_count == 11
    assert not hasattr(result.candidates[0], "metrics")


@pytest.mark.parametrize("disable", ["setting", "fps", "long_gap"])
def test_candidate_tracking_respects_gap_and_metadata_limits(disable):
    extraction = sample_extraction(fps=None if disable == "fps" else 10)
    gap = 4 if disable == "long_gap" else 1
    extraction.source_frame_indices = [i if i < 5 else i + gap for i in range(11)]
    extraction.source_frame_count = 11 + gap
    result = analyze(extraction, candidate_max_gap_seconds=0 if disable == "setting" else .2)
    assert result.repetitions == []
    assert result.candidates == []


def test_missing_hip_is_not_filled_when_candidate_is_tracked():
    extraction = sample_extraction()
    extraction.pose_sequence[4][side_landmarks(BodySide.LEFT)["hip"]].visibility = 0
    result = analyze(extraction)
    assert result.repetitions == []
    assert len(result.candidates) == 1
    assert result.features.hip_y_values[4] is None
    assert result.phases[4] == SquatPhase.UNKNOWN


def test_unobserved_bottom_does_not_become_candidate_from_interpolation():
    extraction = sample_extraction(two_reps=True)
    for index in (5, 6):
        extraction.pose_sequence[index][side_landmarks(BodySide.LEFT)["hip"]].visibility = 0
    result = analyze(extraction)
    assert len(result.repetitions) == 1
    assert result.candidates == []


@pytest.mark.parametrize("seconds", [-1, float("nan"), float("inf")])
def test_invalid_candidate_gap_setting_rejected(seconds):
    with pytest.raises(ValueError, match="finite and nonnegative"):
        analyze(candidate_max_gap_seconds=seconds)
