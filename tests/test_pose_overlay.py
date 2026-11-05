from dataclasses import replace
import json

import pytest

from engine.pose.overlay import build_side_overlay
from engine.pose.side import BodySide, side_landmarks
from engine.squat.response import build_squat_response
from tests.test_squat_remaining_metrics import sample_extraction, analyze


def test_overlay_retains_source_frames_and_only_selected_side_xy():
    extraction = sample_extraction()
    result = build_side_overlay(extraction, BodySide.LEFT)
    assert len(result['frames']) == len(extraction.pose_sequence)
    assert result['frames'][0]['source_frame'] == extraction.source_frame_indices[0]
    assert set(result['frames'][0]['points']) == set(side_landmarks(BodySide.LEFT))
    assert all(point is None or set(point) == {'x', 'y'} for point in result['frames'][0]['points'].values())
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('changes', [dict(visibility=.49), dict(visibility=float('nan')),
                                     dict(x=float('inf')), dict(x=-.1), dict(y=1.1)])
def test_low_visibility_or_invalid_points_are_not_clipped_or_shown(changes):
    extraction = sample_extraction()
    index = side_landmarks(BodySide.LEFT)['knee']
    extraction.pose_sequence[0][index] = replace(extraction.pose_sequence[0][index], **changes)
    result = build_side_overlay(extraction, BodySide.LEFT)
    assert result['frames'][0]['points']['knee'] is None


def test_recovered_pose_is_withheld_and_source_gaps_are_not_filled():
    extraction = sample_extraction()
    extraction.source_frame_indices = [index * 2 for index in extraction.source_frame_indices]
    extraction.source_frame_count = extraction.source_frame_indices[-1] + 1
    extraction.recovered_frame_indices = [0]
    result = build_side_overlay(extraction, BodySide.LEFT)
    assert all(point is None for point in result['frames'][0]['points'].values())
    assert result['frames'][0]['status'] == 'recovered_not_shown'
    assert 1 not in [frame['source_frame'] for frame in result['frames']]


def test_response_overlay_is_explicit_addition_and_does_not_change_measurements():
    extraction = sample_extraction()
    analysis = analyze(extraction)
    plain = build_squat_response(analysis, extraction, source_sha256='a' * 64, facing='left')
    shown = build_squat_response(analysis, extraction, source_sha256='a' * 64, facing='left', include_overlay=True)
    assert 'overlay' not in plain
    assert shown.pop('overlay')['side'] == 'left'
    assert shown == plain
