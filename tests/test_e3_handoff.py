from copy import deepcopy

import pytest

from engine.validation.dataset import read_json, write_new
from engine.validation.handoff import MEASURES, CASES, summarize, build_handoff, scaffold_reference


def result():
    clips = [dict(id=f'clean-{i}', case='compliant', evaluation=dict(
        status='pass', metrics={name: dict(status='pass') for name in MEASURES})) for i in range(3)]
    clips.extend(dict(id=case, case=case, evaluation=dict(status='pass')) for case in CASES)
    return dict(schema_version=1, kind='frozen_primary_evaluation', status='pass',
                dataset_check=dict(ready=True), clips=clips)


def test_complete_evidence_only_prepares_human_review_never_enables_coaching():
    packet = summarize(result())
    assert packet['eligible_for_human_measurement_review'] is True
    assert packet['measurement_approval'] == packet['coaching_approval'] == 'pending'
    assert packet['enabled_rules'] == []


@pytest.mark.parametrize('change', ['smoke', 'quota', 'negative', 'dataset', 'failure', 'missing_metric'])
def test_incomplete_or_development_results_cannot_advance(change):
    data = result()
    if change == 'smoke':
        data['kind'] = 'development_smoke'
    elif change == 'quota':
        data['clips'].pop(0)
    elif change == 'negative':
        data['clips'].pop()
    elif change == 'dataset':
        data['dataset_check']['ready'] = False
    elif change == 'failure':
        data['clips'][0]['evaluation']['metrics']['knee_flexion']['status'] = 'fail'
    else:
        del data['clips'][0]['evaluation']['metrics']['knee_flexion']
    assert summarize(data)['eligible_for_human_measurement_review'] is False


def test_failure_details_and_source_result_preserved(tmp_path):
    data = result()
    item = data['clips'][0]['evaluation']['metrics']['knee_flexion']
    item.update(status='fail', coverage=.5, mean_signed_error=-9)
    original = deepcopy(data)
    path = tmp_path / 'results.json'
    write_new(path, data)
    before = path.read_bytes()
    first = build_handoff(path)
    second = build_handoff(path)
    packet = read_json(first.parent / 'review.json')
    assert first != second
    assert packet['measurement_items']['knee_flexion']['evidence'][0]['details'] == item
    assert packet['actions']
    assert path.read_bytes() == before
    assert data == original


def test_invalid_status_or_duplicate_clip_rejected():
    data = result()
    data['clips'][0]['evaluation']['metrics']['knee_flexion']['status'] = 'approved'
    with pytest.raises(ValueError):
        summarize(data)
    data = result()
    data['clips'].append(deepcopy(data['clips'][0]))
    with pytest.raises(ValueError):
        summarize(data)


def reference():
    return dict(schema_version=1, source_sha256='source', confirmed=True, reviewer='prior', origin='independent_review',
                repetitions=[dict(start_source=i, deepest_interval=[i+3, i+4], end_source=i+8)
                             for i in (2, 12, 22)])


def test_scaffold_never_invents_values_or_confirms_and_does_not_overwrite(tmp_path):
    source, output = tmp_path / 'events.json', tmp_path / 'draft.json'
    write_new(source, reference())
    before = source.read_bytes()
    scaffold_reference(source, output)
    draft = read_json(output)
    assert draft['confirmed'] is False and draft['reviewer'] is None and draft['origin'] is None
    assert len(draft['frame_measurements']) == 30
    assert all(item['value'] is None for item in draft['frame_measurements'])
    assert all(rep['metrics']['knee_flexion']['value'] is None for rep in draft['repetitions'])
    assert source.read_bytes() == before
    with pytest.raises(FileExistsError):
        scaffold_reference(source, output)


def test_scaffold_preserves_existing_independent_values(tmp_path):
    data = reference()
    data['repetitions'][0]['metrics'] = dict(knee_flexion=dict(value=90, uncertainty=1))
    source, output = tmp_path / 'events.json', tmp_path / 'draft.json'
    write_new(source, data)
    scaffold_reference(source, output)
    assert read_json(output)['repetitions'][0]['metrics']['knee_flexion']['value'] == 90


@pytest.mark.parametrize('change', ['short', 'overlap', 'bool'])
def test_scaffold_rejects_invalid_manual_events(tmp_path, change):
    data = reference()
    if change == 'short':
        data['repetitions'].pop()
    elif change == 'overlap':
        data['repetitions'][1]['start_source'] = 5
    else:
        data['repetitions'][0]['start_source'] = True
    source = tmp_path / 'events.json'
    write_new(source, data)
    with pytest.raises(ValueError):
        scaffold_reference(source, tmp_path / 'draft.json')
