from copy import deepcopy

from engine.squat.feedback import build_measurement_feedback
from tests.test_squat_remaining_metrics import analyze, sample_extraction


def by_code(result):
    return {item.code: item for item in build_measurement_feedback(result)}


def test_gap_candidate_is_not_a_measured_cycle_or_metric_reference():
    extraction = sample_extraction()
    extraction.source_frame_indices = [i if i < 5 else i + 1 for i in range(11)]
    extraction.source_frame_count = 12
    notices = by_code(analyze(extraction))
    assert "no_complete_cycles" in notices
    assert "detected_cycles" not in notices
    assert "gap_candidates" in notices
    assert not any(item.references for item in notices.values())


def test_unavailable_metric_preserves_reason_and_one_based_evidence():
    result = analyze(sample_extraction(fps=None))
    notices = by_code(result)
    timing = [ref for ref in notices['unavailable_metrics'].references if ref.metric == 'timing']
    assert len(timing) == 1
    assert timing[0].repetition == 1
    assert timing[0].reason == result.repetitions[0].metrics['timing'].quality.reason


def test_recovery_generates_review_not_an_accuracy_score():
    extraction = sample_extraction()
    extraction.recovered_frame_indices = [5]
    notices = by_code(analyze(extraction))
    assert "recovered_observations" in notices
    assert "partial_metrics" in notices
    assert all(ref.repetition == 1 for ref in notices['recovered_observations'].references)
    assert 'measurement_scope' in notices


def test_experimental_calibration_is_explicit():
    result = analyze(use_posture_calibration=True, use_robust_fallback=True)
    assert "experimental_calibration" in by_code(result)
    assert "experimental_calibration" not in by_code(analyze())


def test_feedback_is_deterministic_and_does_not_modify_analysis():
    result = analyze(sample_extraction(two_reps=True))
    before = deepcopy(result)
    assert build_measurement_feedback(result) == build_measurement_feedback(result)
    assert result == before
    assert all(ref.repetition in (1, 2) for item in build_measurement_feedback(result) for ref in item.references)
