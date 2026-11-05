from dataclasses import replace

import pytest

from engine.squat.feedback import FeedbackCard
from engine.squat.personal import build_baseline, compare_baseline, summarize_session, save_baseline, load_baseline


CONTEXT = dict(profile_sha256='a' * 64, pipeline_sha256='b' * 64, setup_id='fixed-camera', side='left', facing='left')


def cards():
    return [FeedbackCard(i, 'knee_flexion', None, 'observation', value, 'degrees', 'reviewed', 'Inspect video.')
            for i, value in enumerate((80., 90., 100.), 1)]


def baseline(items=None, reviewer='fixture'):
    return build_baseline(cards() if items is None else items, context=CONTEXT, source_sha256='c' * 64, reviewer=reviewer)


def test_baseline_is_descriptive_median_range_and_serializable(tmp_path):
    result = baseline()
    item = next(item for item in result['items'] if item['metric'] == 'knee_flexion')
    assert (item['minimum'], item['median'], item['maximum']) == (80, 90, 100)
    path = tmp_path / 'baseline.json'
    save_baseline(result, path)
    assert load_baseline(path) == result
    with pytest.raises(FileExistsError):
        save_baseline(result, path)
    assert result['coaching_status'] == 'pending_validation'


def test_comparison_keeps_signed_difference_without_judgment():
    result = compare_baseline(cards(), baseline(), context=CONTEXT)
    assert [item['difference_from_preparation_median'] for item in result] == [-10, 0, 10]
    assert all(item['status'] == 'descriptive_comparison' for item in result)


@pytest.mark.parametrize('field,value', [('profile_sha256', 'd' * 64), ('pipeline_sha256', 'd' * 64),
                                      ('side', 'right'), ('facing', 'right'), ('setup_id', 'other-camera')])
def test_context_changes_block_comparison(field, value):
    result = compare_baseline(cards(), baseline(), context={**CONTEXT, field: value})
    assert all(item['status'] == 'context_mismatch' and item['difference_from_preparation_median'] is None for item in result)


@pytest.mark.parametrize('mode', ['quota', 'missing', 'reviewer', 'nan'])
def test_incomplete_baseline_does_not_become_personal_standard(mode):
    items = cards()
    if mode == 'quota':
        items.pop()
    elif mode == 'missing':
        items[0] = replace(items[0], status='capture_review', observation=None)
    elif mode == 'nan':
        items[0] = replace(items[0], observation=float('nan'))
    result = compare_baseline(cards(), baseline(items, None if mode == 'reviewer' else 'fixture'), context=CONTEXT)
    assert all(item['status'] == 'baseline_unavailable' for item in result)


def test_bad_current_observation_and_corrupt_baseline_withheld():
    assert compare_baseline([replace(cards()[0], status='measurement_review')], baseline(), context=CONTEXT)[0]['status'] == 'observation_unavailable'
    data = baseline()
    next(item for item in data['items'] if item['metric'] == 'knee_flexion')['median'] = float('inf')
    with pytest.raises(ValueError):
        compare_baseline(cards(), data, context=CONTEXT)


def test_duplicate_cycles_rejected():
    with pytest.raises(ValueError):
        baseline(cards() + [cards()[0]])


def test_session_actions_deduplicate_and_keep_evidence():
    items = cards() + [replace(cards()[0], status='retake', action='Record again.')]
    summary = summarize_session(items)
    assert summary[0]['status'] == 'retake'
    assert summary[1]['repetitions'] == [1, 2, 3]
    assert len(summary[1]['evidence']) == 3
    assert summarize_session([]) == []


def test_report_rejects_stale_runtime_before_processing(tmp_path, monkeypatch):
    from tools import review_samples
    from engine.pose.orientation import FacingDirection
    monkeypatch.setattr(review_samples, 'personal_pipeline_signature', lambda *args: 'f' * 64)
    with pytest.raises(ValueError, match='pipeline'):
        review_samples.review_video(tmp_path / 'missing.mp4', FacingDirection.LEFT, tmp_path / 'output',
                                    personal_baseline=baseline(), personal_context=CONTEXT)
