import json

import pytest

from engine.squat.response import build_squat_response
from tests.test_squat_remaining_metrics import analyze, sample_extraction


def response(analysis=None, extraction=None, **kwargs):
    extraction = extraction or sample_extraction()
    analysis = analysis or analyze(extraction)
    return build_squat_response(analysis, extraction, source_sha256='a' * 64, facing='left', **kwargs)


def test_response_is_json_and_preserves_withholding_and_source_boundaries():
    extraction = sample_extraction()
    analysis = analyze(extraction)
    result = response(analysis, extraction)
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert result['overview']['state'] == 'capture_review'
    assert result['interpretation']['coaching'] == 'pending_validation'
    assert result['repetitions'][0]['source_frames']['start'] == extraction.source_frame_indices[analysis.repetitions[0].rep.start_index]
    assert 'pose_sequence' not in result and 'video' not in result['source']


def test_response_is_detached_from_analysis():
    extraction = sample_extraction()
    analysis = analyze(extraction)
    result = response(analysis, extraction)
    result['provenance']['issues'].append('client mutation')
    assert 'client mutation' not in analysis.issues
    result['repetitions'][0]['metrics']['knee_flexion']['value'] = -999
    assert analysis.repetitions[0].metrics['knee_flexion'].value != -999


def test_sparse_source_frames_and_candidates_remain_explicit():
    from copy import deepcopy
    from engine.squat.analyzer import SquatRepCandidate
    extraction = sample_extraction()
    rep = deepcopy(analyze(extraction).repetitions[0].rep)
    extraction.source_frame_indices = [index * 2 for index in extraction.source_frame_indices]
    extraction.source_frame_count = extraction.source_frame_indices[-1] + 1
    analysis = analyze(extraction)
    analysis.candidates.clear()
    analysis.candidates.append(SquatRepCandidate(rep, rep.bottom_index, 1))
    result = response(analysis, extraction)
    assert len(result['repetitions']) == len(analysis.repetitions)
    assert len(result['candidates']) == 1
    assert 'metrics' not in result['candidates'][0]
    assert result['candidates'][0]['observed_bottom'] == extraction.source_frame_indices[rep.bottom_index]


def test_no_cycles_returns_empty_repetitions_not_an_error():
    analysis = analyze()
    analysis.repetitions.clear()
    result = response(analysis)
    assert result['repetitions'] == []
    assert result['overview']['state'] == 'no_complete_cycles'


def test_nonfinite_raw_metric_rejected_instead_of_emitting_invalid_json():
    analysis = analyze()
    analysis.repetitions[0].metrics['knee_flexion'].value = float('nan')
    with pytest.raises(ValueError):
        response(analysis)


def test_mismatched_frames_or_invalid_indices_rejected():
    analysis = analyze()
    analysis.phases.pop()
    with pytest.raises(ValueError, match='frame counts'):
        response(analysis)
    analysis = analyze()
    analysis.repetitions[0].rep.end_index = 9999
    with pytest.raises(ValueError):
        response(analysis)


@pytest.mark.parametrize('changes', [dict(source_sha256='bad'), dict(facing='auto')])
def test_source_and_selection_must_be_explicit(changes):
    options = dict(source_sha256='a' * 64, facing='left')
    options.update(changes)
    with pytest.raises(ValueError):
        build_squat_response(analyze(), sample_extraction(), **options)
