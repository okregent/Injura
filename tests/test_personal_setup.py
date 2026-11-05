import json
from dataclasses import asdict

import pytest

from engine.validation.dataset import read_json
from tests.test_body_profile import profile
from tests.test_measurement_rules import APPROVED
from tests.test_e3_workflow import three_cycle_extraction
from tools import personal_setup as setup


def update(path, **changes):
    value = read_json(path)
    value.update(changes)
    path.write_text(json.dumps(value), encoding='utf-8')


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    first, second = tmp_path / 'profile.mp4', tmp_path / 'preparation.mp4'
    first.write_bytes(b'fictional-profile')
    second.write_bytes(b'fictional-preparation')
    root = tmp_path / 'setup'
    setup.prepare(first, second, root)
    monkeypatch.setattr(setup, 'decoded_frame_exists', lambda *args: True)
    monkeypatch.setattr(setup, 'personal_pipeline_signature', lambda: 'b' * 64)
    return root


def complete(root):
    from dataclasses import replace
    manifest = read_json(root / 'manifest.json')
    data = asdict(replace(profile(), source_sha256=manifest['profile_source_sha256']))
    (root / 'profile.json').write_text(json.dumps(data), encoding='utf-8')
    update(root / 'manifest.json', side='left', facing='left', setup_id='fixture',
           setup_reviewed=True, same_person_confirmed=True, baseline_reviewer='fixture')
    update(root / 'recording-review.json', reviews=[asdict(APPROVED)])


def test_fresh_setup_is_unapproved_and_does_not_overwrite(bundle):
    assert setup.check(bundle)['ready'] is False
    assert read_json(bundle / 'profile.json')['thigh']['pixels'] is None
    manifest = read_json(bundle / 'manifest.json')
    with pytest.raises(FileExistsError):
        setup.prepare(manifest['profile_video'], manifest['preparation_video'], bundle)
    with pytest.raises(ValueError, match='not ready'):
        setup.build(bundle, extractor=lambda _: pytest.fail('must not infer'))


def test_reviewed_setup_builds_source_bound_descriptive_snapshot(bundle):
    complete(bundle)
    assert setup.check(bundle)['ready'] is True
    output = setup.build(bundle, extractor=lambda _: three_cycle_extraction())
    baseline = read_json(output / 'baseline.json')
    evidence = read_json(output / 'evidence.json')
    assert baseline['coaching_status'] == 'pending_validation'
    assert evidence['complete_cycles'] == 3
    assert evidence['descriptive_items'] > 0
    assert baseline['context'] == read_json(output / 'context.json')


@pytest.mark.parametrize('change', ['source', 'identity', 'frame', 'side', 'capture'])
def test_missing_or_changed_evidence_blocks_setup(bundle, monkeypatch, change):
    complete(bundle)
    if change == 'source':
        manifest = read_json(bundle / 'manifest.json')
        from pathlib import Path
        Path(manifest['profile_video']).write_bytes(b'changed')
    elif change == 'identity':
        update(bundle / 'manifest.json', same_person_confirmed=None)
    elif change == 'frame':
        monkeypatch.setattr(setup, 'decoded_frame_exists', lambda *args: False)
    elif change == 'side':
        update(bundle / 'manifest.json', side='right')
    else:
        update(bundle / 'recording-review.json', reviews=[])
    assert setup.check(bundle)['ready'] is False


def test_source_changed_during_extraction_leaves_no_baseline(bundle):
    complete(bundle)
    def mutate(video):
        video.write_bytes(b'changed-during-inference')
        return three_cycle_extraction()
    with pytest.raises(ValueError):
        setup.build(bundle, extractor=mutate)
    assert not (bundle / 'runs').exists()


def test_status_view_escapes_untrusted_text(bundle):
    update(bundle / 'manifest.json', schema_version='<script>')
    page = setup.status(bundle)
    assert '<script>' not in page.read_text(encoding='utf-8')
