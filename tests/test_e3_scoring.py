from copy import deepcopy
from dataclasses import replace

import pytest

from engine.validation.scoring import decision, match_cycles, summarize_pairs, score_compliant, score_violation
from engine.validation.dataset import read_json, PROTOCOL
from tests.test_measurement_rules import APPROVED
from tests.test_squat_remaining_metrics import analyze, sample_extraction


def test_equal_counts_with_nonoverlapping_cycles_do_not_match():
    assert match_cycles([dict(start_source=50, end_source=60)], [dict(start_source=1, end_source=10)]) == {}


def test_one_prediction_never_matches_two_references():
    matches = match_cycles([dict(start_source=0, end_source=20)],
                           [dict(start_source=0, end_source=10), dict(start_source=10, end_source=20)])
    assert matches == {0: 0}


def test_missing_predicted_values_stay_in_coverage_denominator():
    pairs = [dict(reference=0, observed=0, ready=True)] * 8 + [dict(reference=0, observed=None, ready=False)] * 2
    result = summarize_pairs(pairs, dict(max_mean_absolute_error=5, max_absolute_error=10))
    assert result['coverage'] == .8
    assert result['status'] == 'fail'
    assert result['mean_absolute_error'] == 0


def test_error_thresholds_require_both_mean_and_maximum():
    pairs = [dict(reference=0, observed=0, ready=True)] * 9 + [dict(reference=0, observed=11, ready=True)]
    assert summarize_pairs(pairs, dict(max_mean_absolute_error=5, max_absolute_error=10))['status'] == 'fail'
    pairs[-1]['observed'] = 10
    assert summarize_pairs(pairs, dict(max_mean_absolute_error=5, max_absolute_error=10))['status'] == 'pass'


def test_unresolved_reference_or_missing_quota_does_not_pass():
    assert summarize_pairs([dict(reference=None, observed=1, ready=True)], {})['status'] == 'not_evaluated'
    assert summarize_pairs([dict(reference=1, observed=1, ready=True)], {}, minimum_samples=10)['status'] == 'not_evaluated'
    assert decision([]) == 'not_evaluated'
    with pytest.raises(ValueError):
        decision(['unknown'])


def test_unconfirmed_reference_is_not_graded_and_does_not_mutate_analysis():
    ex = sample_extraction()
    analysis = analyze(ex)
    before = deepcopy(analysis)
    result = score_compliant(analysis, ex, dict(confirmed=False), APPROVED, read_json(PROTOCOL))
    assert result['status'] == 'not_evaluated'
    assert analysis == before


def test_synthetic_matching_uses_source_frames_not_pose_positions():
    ex = sample_extraction()
    # A uniformly shifted source window remains uninterrupted but has distinct indices.
    ex.source_frame_indices = [i + 100 for i in range(11)]
    ex.source_frame_count = 111
    analysis = analyze(ex)
    reference = dict(confirmed=True, origin='independent_review', reviewer='synthetic-only',
                     repetitions=[dict(start_source=102, deepest_interval=[105, 106], end_source=110, metrics={})],
                     frame_measurements=[])
    result = score_compliant(analysis, ex, reference, APPROVED, read_json(PROTOCOL))
    assert result['metrics']['complete_repetitions']['status'] == 'pass'
    assert result['metrics']['start_boundary']['max_absolute_error'] == 0
    assert result['metrics']['deepest_observed_frame']['max_absolute_error'] == 0
    assert result['status'] == 'not_evaluated'


def test_candidate_does_not_turn_into_a_count_match():
    ex = sample_extraction()
    ex.source_frame_indices = [i if i < 5 else i + 1 for i in range(11)]
    ex.source_frame_count = 12
    analysis = analyze(ex)
    reference = dict(confirmed=True, origin='independent_review', reviewer='synthetic-only',
                     repetitions=[dict(start_source=2, deepest_interval=[6, 7], end_source=11, metrics={})], frame_measurements=[])
    result = score_compliant(analysis, ex, reference, APPROVED, read_json(PROTOCOL))
    counts = result['metrics']['complete_repetitions']
    assert counts['missed'] == 1 and counts['excluded_candidates'] == 1
    assert result['status'] == 'fail'


def test_inconsistent_phase_sum_is_not_hidden_by_valid_total_duration():
    ex = sample_extraction()
    analysis = analyze(ex)
    outcome = analysis.repetitions[0].metrics['timing']
    outcome.value = replace(outcome.value, bottom_seconds=outcome.value.bottom_seconds + 1)
    reference = dict(confirmed=True, origin='independent_review', reviewer='synthetic-only',
                     repetitions=[dict(start_source=2, deepest_interval=[5, 6], end_source=10, metrics={})], frame_measurements=[])
    result = score_compliant(analysis, ex, reference, APPROVED, read_json(PROTOCOL))
    assert result['metrics']['phase_duration_arithmetic']['status'] == 'fail'
    assert result['status'] == 'fail'


def test_timing_violation_preserves_angle_eligibility_and_raw_result():
    analysis = analyze()
    review = replace(APPROVED, constant_frame_rate=False)
    before = deepcopy(analysis)
    result = score_violation(analysis, review, ['total_duration'], ['knee_flexion'])
    assert result['status'] == 'pass'
    assert result['eligibility_checks'][0]['actual_gate_status'] == 'rejected'
    assert analysis == before
