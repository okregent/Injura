import json
from dataclasses import asdict, replace

import pytest

from engine.pose.side import BodySide
from engine.squat.recording import RecordingReview, recording_gate, load_recording_reviews
from engine.squat.rules import evaluate_rules
from tests.test_measurement_rules import APPROVED, rule
from tests.test_squat_remaining_metrics import analyze


def test_missing_and_negative_review_remain_distinct():
    assert recording_gate('knee_flexion', None, BodySide.LEFT) == ('unknown', 'recording_review_missing')
    status, reason = recording_gate('knee_flexion', replace(APPROVED, side_view=False), BodySide.LEFT)
    assert status == 'rejected'
    assert reason.endswith(':side_view')
    status, reason = recording_gate('knee_flexion', replace(APPROVED, side_view=None), BodySide.LEFT)
    assert status == 'unknown'
    assert reason.endswith(':side_view')


def test_incomplete_or_wrong_side_review_is_not_approval():
    for review in [replace(APPROVED, side='right'), replace(APPROVED, reviewer=None)]:
        assert recording_gate('knee_flexion', review, BodySide.LEFT)[0] == 'unknown'


def test_failed_timing_conditions_do_not_reject_visible_joint_angle():
    review = replace(APPROVED, continuous_original_speed=False)
    assert recording_gate('timing', review, BodySide.LEFT)[0] == 'rejected'
    assert recording_gate('knee_flexion', review, BodySide.LEFT)[0] == 'approved'


def test_unreviewed_foot_does_not_reject_torso_measurement():
    review = replace(APPROVED, shoulders_visible=True)
    assert recording_gate('normalized_knee_travel', review, BodySide.LEFT)[0] == 'unknown'
    assert recording_gate('torso_lean', review, BodySide.LEFT)[0] == 'approved'


def test_known_rejection_precedes_other_unknown_conditions():
    review = replace(APPROVED, side_view=None, camera_fixed=False)
    assert recording_gate('depth', review, BodySide.LEFT) == ('rejected', 'recording_review_rejected:camera_fixed')


@pytest.mark.parametrize('value', [1, 'true', [], {}])
def test_review_flags_require_actual_boolean_or_null(value):
    with pytest.raises(ValueError):
        RecordingReview('left', side_view=value)


def test_rule_is_withheld_without_review_and_raw_metrics_preserved():
    result = analyze()
    original = result.repetitions[0].metrics['knee_flexion'].value
    item, = evaluate_rules(result, [rule(threshold=0)])
    assert item.status == 'withheld'
    assert item.reason == 'recording_review_missing'
    assert item.message is None
    assert result.repetitions[0].metrics['knee_flexion'].value == original
    approved, = evaluate_rules(result, [rule(threshold=0)], recording_review=APPROVED)
    assert approved.status == 'matched'


def test_source_bound_review_rejects_wrong_or_changed_video(tmp_path):
    video = tmp_path / 'sample.mp4'
    video.write_bytes(b'example')
    data = dict(video=video.name, size=video.stat().st_size,
                mtime_ns=video.stat().st_mtime_ns, reviews=[asdict(APPROVED)])
    path = tmp_path / 'review.json'
    path.write_text(json.dumps(data))
    assert load_recording_reviews(path, video) == [APPROVED]
    video.write_bytes(b'changed source')
    with pytest.raises(ValueError, match='signature'):
        load_recording_reviews(path, video)


def test_duplicate_side_reviews_rejected(tmp_path):
    video = tmp_path / 'sample.mp4'
    video.write_bytes(b'example')
    path = tmp_path / 'review.json'
    path.write_text(json.dumps(dict(video=video.name, size=video.stat().st_size,
                                   mtime_ns=video.stat().st_mtime_ns,
                                   reviews=[asdict(APPROVED), asdict(APPROVED)])))
    with pytest.raises(ValueError, match='duplicate'):
        load_recording_reviews(path, video)


def test_template_is_unknown_and_never_overwrites_existing_review(tmp_path):
    from tools.prepare_recording_review import prepare
    video = tmp_path / 'sample.mp4'
    video.write_bytes(b'example')
    output = tmp_path / 'review.json'
    prepare(video, output)
    reviews = load_recording_reviews(output, video)
    assert all(recording_gate('depth', review, BodySide(review.side))[0] == 'unknown' for review in reviews)
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        prepare(video, output)
    assert output.read_bytes() == before
