import json
from dataclasses import asdict, fields

import pytest

from engine.squat.recording import RecordingReview
from engine.validation import dataset


def save(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def reference(entry):
    reps = [dict(start_source=start, deepest_interval=[start + 3, start + 4], end_source=start + 8,
                 uncertainty_frames=0, metrics={name: dict(value=1.0, uncertainty=0) for name in dataset.METRICS})
            for start in (2, 12, 22)]
    positions = dataset.reference_positions(reps)
    return dict(source_sha256=entry['sha256'], confirmed=True, reviewer='synthetic-fixture-only',
                origin='independent_review', repetitions=reps,
                frame_measurements=[dict(metric=name, source_frame=frame, value=1.0, uncertainty=0)
                                    for name in dataset.FRAME_METRICS for frame in positions])


@pytest.fixture
def ready_bundle(tmp_path):
    """Fictitious byte sources and labels test lifecycle, never real accuracy."""
    videos = []
    for i in range(6):
        video = tmp_path / f'fictional-{i}.mp4'
        video.write_bytes(f'not a real video; lifecycle fixture {i}'.encode())
        videos.append(video)
    root = tmp_path / 'bundle'
    dataset.prepare(videos, root)
    manifest = dataset.read_json(root / 'manifest.json')
    for i, entry in enumerate(manifest['clips']):
        entry.update(participant_id=f'fictional-{i}', source_group_id=f'fictional-group-{i}',
                     provenance_reviewed=True, unused_for_development=True, side='left', facing='right')
        review = {field.name: True for field in fields(RecordingReview) if field.name not in ('side', 'reviewer', 'notes')}
        review.update(side='left', reviewer='synthetic-fixture-only', notes='No real participant/accuracy evidence')
        if i == 3:
            entry.update(case='wrong_view', expected_affected_items=[*dataset.METRICS, 'total_duration'], expected_unaffected_items=[])
            review['side_view'] = False
        if i == 4:
            entry.update(case='required_joint_occlusion',
                         expected_affected_items=['knee_flexion', 'hip_flexion', 'hip_to_knee_gap', 'raw_knee_travel', 'foot_normalized_knee_travel'],
                         expected_unaffected_items=['torso_lean', 'relative_descent', 'heel_rise_magnitude', 'total_duration'])
            review['knees_visible'] = False
        if i == 5:
            entry.update(case='timing_discontinuity_or_unknown_cadence', expected_affected_items=['total_duration'], expected_unaffected_items=list(dataset.METRICS))
            review['constant_frame_rate'] = None
        path = root / entry['recording_review']
        data = dataset.read_json(path)
        data['reviews'] = [review]
        save(path, data)
        save(root / entry['reference'], reference(entry))
    save(root / 'manifest.json', manifest)
    return root


def test_registration_is_unknown_and_existing_directory_is_preserved(tmp_path):
    video = tmp_path / 'draft.mp4'
    video.write_bytes(b'fixture')
    root = tmp_path / 'draft'
    dataset.prepare([video], root)
    report = dataset.check(root)
    assert report['ready'] is False
    assert not any('negative case' in problem for problem in report['clips'][0]['problems'])
    item = dataset.read_json(root / 'references/clip-001.json')
    assert item['confirmed'] is False and item['repetitions'] == []
    before = (root / 'manifest.json').read_bytes()
    with pytest.raises(FileExistsError):
        dataset.prepare([video], root)
    assert (root / 'manifest.json').read_bytes() == before


def test_known_development_content_is_blocked_after_rename(tmp_path, monkeypatch):
    video = tmp_path / 'renamed.mp4'
    video.write_bytes(b'known development source')
    original = dataset.read_json
    monkeypatch.setattr(dataset, 'read_json', lambda p: dict(sources=[dict(id='dev', sha256=dataset.sha256(video))], primary_configuration=original(dataset.INVENTORY)['primary_configuration'])
                        if p == dataset.INVENTORY else original(p))
    root = tmp_path / 'bundle'
    dataset.prepare([video], root)
    report = dataset.check(root)
    assert any('known development' in problem for problem in report['clips'][0]['problems'])


def test_complete_synthetic_lifecycle_inputs_are_ready(ready_bundle):
    assert dataset.check(ready_bundle)['ready'] is True


@pytest.mark.parametrize('mutation', ['video', 'reference', 'review', 'limits', 'manifest'])
def test_frozen_input_changes_are_rejected(ready_bundle, mutation):
    dataset.freeze(ready_bundle)
    manifest = dataset.verify_frozen(ready_bundle)
    targets = {'video': manifest['clips'][0]['video'],
               'reference': ready_bundle / manifest['clips'][0]['reference'],
               'review': ready_bundle / manifest['clips'][0]['recording_review'],
               'limits': ready_bundle / 'limits.json', 'manifest': ready_bundle / 'manifest.json'}
    from pathlib import Path
    path = Path(targets[mutation])
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError, match='changed'):
        dataset.verify_frozen(ready_bundle)


def test_freeze_does_not_overwrite_and_code_runtime_changes_reject(ready_bundle, monkeypatch):
    dataset.freeze(ready_bundle)
    with pytest.raises(FileExistsError):
        dataset.freeze(ready_bundle)
    monkeypatch.setattr(dataset, 'analysis_fingerprint', lambda: 'changed-code')
    with pytest.raises(ValueError, match='analysis source'):
        dataset.verify_frozen(ready_bundle)


def test_runtime_and_weights_are_frozen(ready_bundle, monkeypatch):
    dataset.freeze(ready_bundle)
    monkeypatch.setattr(dataset, 'environment_signature', lambda: dict(full_model_sha256='other-weights'))
    with pytest.raises(ValueError, match='runtime'):
        dataset.verify_frozen(ready_bundle)


@pytest.mark.parametrize('mutation', ['uncertainty', 'sample_quota', 'source_hash', 'unconfirmed', 'unknown_source'])
def test_bad_references_do_not_freeze(ready_bundle, mutation):
    path = ready_bundle / 'references/clip-001.json'
    data = dataset.read_json(path)
    if mutation == 'uncertainty':
        data['repetitions'][0]['metrics']['knee_flexion']['uncertainty'] = 99
    elif mutation == 'sample_quota':
        data['frame_measurements'].pop()
    elif mutation == 'source_hash':
        data['source_sha256'] = 'wrong'
    elif mutation == 'unconfirmed':
        data['confirmed'] = False
    else:
        manifest = dataset.read_json(ready_bundle / 'manifest.json')
        manifest['clips'][0]['provenance_reviewed'] = None
        save(ready_bundle / 'manifest.json', manifest)
    save(path, data)
    assert dataset.check(ready_bundle)['ready'] is False
    with pytest.raises(ValueError, match='not ready'):
        dataset.freeze(ready_bundle)


def test_bundle_paths_cannot_escape(tmp_path):
    with pytest.raises(ValueError, match='escapes'):
        dataset.local_path(tmp_path, '../outside.json')


def test_frozen_ledger_cannot_silently_omit_an_input(ready_bundle):
    dataset.freeze(ready_bundle)
    path = ready_bundle / 'freeze.json'
    data = dataset.read_json(path)
    data['files'].pop('references/clip-001.json')
    save(path, data)
    with pytest.raises(ValueError, match='ledger'):
        dataset.verify_frozen(ready_bundle)


def test_evaluation_logic_is_frozen_too(ready_bundle, monkeypatch):
    dataset.freeze(ready_bundle)
    monkeypatch.setattr(dataset, 'evaluation_fingerprint', lambda: 'changed-evaluator')
    with pytest.raises(ValueError, match='evaluation source'):
        dataset.verify_frozen(ready_bundle)


def test_case_names_require_consistent_human_review(ready_bundle):
    path = ready_bundle / 'reviews/clip-004.json'
    data = dataset.read_json(path)
    data['reviews'][0]['side_view'] = True
    save(path, data)
    report = dataset.check(ready_bundle)
    assert not report['ready']
    assert any('explicitly rejected view' in issue for issue in report['clips'][3]['problems'])


def test_duplicate_content_is_rejected_before_creating_bundle(tmp_path):
    a, b = tmp_path / 'a.mp4', tmp_path / 'b.mp4'
    a.write_bytes(b'identical')
    b.write_bytes(b'identical')
    with pytest.raises(ValueError, match='duplicate'):
        dataset.prepare([a, b], tmp_path / 'bundle')
    assert not (tmp_path / 'bundle').exists()


def test_register_preserves_existing_reference_and_rejects_frozen_or_duplicate_sources(ready_bundle, tmp_path):
    existing = (ready_bundle / 'references/clip-001.json').read_bytes()
    video = tmp_path / 'additional.mp4'
    video.write_bytes(b'additional lifecycle fixture')
    dataset.register([video], ready_bundle)
    manifest = dataset.read_json(ready_bundle / 'manifest.json')
    assert len(manifest['clips']) == 7
    backups = list(ready_bundle.glob('manifest.before-register-*.json'))
    assert len(backups) == 1 and len(dataset.read_json(backups[0])['clips']) == 6
    assert (ready_bundle / 'references/clip-001.json').read_bytes() == existing
    assert manifest['clips'][-1]['side'] is None
    assert dataset.read_json(ready_bundle / manifest['clips'][-1]['reference'])['confirmed'] is False
    with pytest.raises(ValueError, match='duplicate'):
        dataset.register([video], ready_bundle)
    (ready_bundle / 'freeze.json').write_text('{}')
    with pytest.raises(ValueError, match='frozen'):
        dataset.register([video], ready_bundle)
