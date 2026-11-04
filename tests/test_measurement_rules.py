import json
from dataclasses import replace

import pytest

from engine.squat.rules import MeasurementRule, evaluate_rules, load_rules
from engine.squat.recording import RecordingReview
from tests.test_squat_remaining_metrics import analyze, sample_extraction

APPROVED = RecordingReview('left', reviewer='test', side_view=True, camera_fixed=True,
                           subject_clear=True, hips_visible=True, knees_visible=True,
                           ankles_visible=True, continuous_original_speed=True, constant_frame_rate=True)


def rule(**kwargs):
    defaults = dict(id="test", metric="knee_flexion", field=None, comparator="gt",
                    threshold=20, message="configured condition", enabled=True)
    defaults.update(kwargs)
    return MeasurementRule(**defaults)


@pytest.mark.parametrize("comparator,expected", [("gt", False), ("gte", True), ("lt", False),
                                                ("lte", True), ("eq", True), ("ne", False)])
def test_comparison_boundary_semantics_and_evidence(comparator, expected):
    result = analyze()
    result.repetitions[0].metrics['knee_flexion'].value = 20.0
    item, = evaluate_rules(result, [rule(comparator=comparator)], recording_review=APPROVED)
    assert item.status == ('matched' if expected else 'not_matched')
    assert item.value == 20.0
    assert item.unit == 'degrees'
    assert item.repetition == 1
    assert item.message == ('configured condition' if expected else None)


@pytest.mark.parametrize("changes", [dict(metric="unknown"), dict(field="__class__"),
                                     dict(comparator="eval"), dict(threshold=float('nan')),
                                     dict(threshold=True), dict(enabled=1)])
def test_invalid_rules_rejected(changes):
    with pytest.raises(ValueError):
        rule(**changes)


def test_disabled_by_default_and_no_rules_produce_no_evaluations():
    result = analyze()
    assert evaluate_rules(result, []) == []
    disabled = MeasurementRule('off', 'knee_flexion', None, 'gt', 0, 'unused')
    item, = evaluate_rules(result, [disabled])
    assert item.status == 'disabled'
    assert item.message is None


@pytest.mark.parametrize('mode', ['missing_fps', 'recovery', 'experimental', 'nonfinite'])
def test_unsupported_measurements_are_withheld(mode):
    extraction = sample_extraction(fps=None if mode == 'missing_fps' else 10)
    if mode == 'recovery':
        extraction.recovered_frame_indices = [5]
    result = analyze(extraction, **(dict(use_posture_calibration=True, use_robust_fallback=True)
                                   if mode == 'experimental' else {}))
    selected = rule(metric='timing', field='total_seconds', threshold=0)
    if mode == 'nonfinite':
        outcome = result.repetitions[0].metrics['timing']
        outcome.value = replace(outcome.value, total_seconds=float('inf'))
    item, = evaluate_rules(result, [selected], recording_review=APPROVED)
    assert item.status == 'withheld'
    assert item.reason
    assert item.message is None
    assert item.value is None


def test_candidates_are_not_evaluated():
    extraction = sample_extraction()
    extraction.source_frame_indices = [i if i < 5 else i + 1 for i in range(11)]
    extraction.source_frame_count = 12
    result = analyze(extraction)
    assert result.candidates
    assert evaluate_rules(result, [rule()]) == []


def test_config_rejects_unknown_fields_and_duplicate_ids(tmp_path):
    path = tmp_path / 'rules.json'
    path.write_text(json.dumps({'rules': [dict(id='x', unknown=True)]}))
    with pytest.raises(ValueError):
        load_rules(path)
    with pytest.raises(ValueError, match='duplicate'):
        evaluate_rules(analyze(), [rule(), rule()])


def test_json_round_trip_and_default_empty_configuration(tmp_path):
    from dataclasses import asdict
    path = tmp_path / 'rules.json'
    path.write_text(json.dumps({'rules': [asdict(rule())]}))
    assert load_rules(path) == [rule()]
    assert load_rules('engine/squat/squat_rules.json') == []
