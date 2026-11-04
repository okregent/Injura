import json
from copy import deepcopy

import pytest

from engine.validation import dataset
from tests.test_e3_dataset import ready_bundle
from tests.test_squat_remaining_metrics import sample_extraction
from tools.evaluate_e3 import run, build_status


def three_cycle_extraction():
    result = sample_extraction(two_reps=True)
    result.pose_sequence.extend(deepcopy(sample_extraction().pose_sequence[1:]))
    result.source_frame_indices = list(range(len(result.pose_sequence)))
    result.source_frame_count = len(result.pose_sequence)
    return result


def test_smoke_run_never_declares_acceptance_or_uses_reference_truth(ready_bundle):
    result_path = run(ready_bundle, smoke=True, extractor=lambda _: three_cycle_extraction())
    result = dataset.read_json(result_path.parent / 'results.json')
    assert result['kind'] == 'development_smoke'
    assert result['status'] == 'not_evaluated'
    assert all(clip['evaluation']['status'] == 'not_evaluated' for clip in result['clips'])
    assert 'not_evaluated' in result_path.read_text()


def test_frozen_pipeline_writes_evidence_with_no_real_accuracy_claim(ready_bundle):
    dataset.freeze(ready_bundle)
    page = run(ready_bundle, extractor=lambda _: three_cycle_extraction())
    result = dataset.read_json(page.parent / 'results.json')
    # Lifecycle fixtures intentionally contain arbitrary numeric references.
    assert result['status'] == 'fail'
    assert all(clip['evaluation']['metrics']['complete_repetitions']['status'] == 'pass' for clip in result['clips'][:3])
    assert all(clip['evaluation']['status'] == 'pass' for clip in result['clips'][3:])
    assert 'runtime' in result
    assert (page.parent / 'results.json').is_file()


def test_primary_run_refuses_unfrozen_bundle(ready_bundle):
    with pytest.raises(FileNotFoundError):
        run(ready_bundle, extractor=lambda _: three_cycle_extraction())


def test_development_smoke_exposure_blocks_new_bundle_with_same_content(ready_bundle):
    run(ready_bundle, smoke=True, extractor=lambda _: three_cycle_extraction())
    source = dataset.read_json(ready_bundle / 'manifest.json')['clips'][0]['video']
    other = ready_bundle.parent / 'renamed-bundle'
    dataset.prepare([source], other)
    report = dataset.check(other)
    assert any('known development' in issue for issue in report['clips'][0]['problems'])
    assert dataset.check(ready_bundle)['ready'] is False


def test_frozen_bundle_rejects_development_smoke(ready_bundle):
    dataset.freeze(ready_bundle)
    with pytest.raises(ValueError, match='cannot be run on a frozen'):
        run(ready_bundle, smoke=True, extractor=lambda _: three_cycle_extraction())


def test_status_dashboard_never_converts_smoke_into_acceptance(ready_bundle):
    run(ready_bundle, smoke=True, extractor=lambda _: three_cycle_extraction())
    page = build_status(ready_bundle.parent)
    status = dataset.read_json(page.parent / 'status.json')
    assert status[0]['latest_kind'] == 'development_smoke'
    assert status[0]['latest_decision'] == 'not_evaluated'
    assert (page.parent / status[0]['latest_link']).is_file()


def test_changed_source_during_inference_does_not_publish_results(ready_bundle):
    dataset.freeze(ready_bundle)
    def changed_source(video):
        video.write_bytes(b'changed during inference')
        return three_cycle_extraction()
    with pytest.raises(ValueError, match='changed'):
        run(ready_bundle, extractor=changed_source)
    assert not list((ready_bundle / 'runs').glob('*/results.json'))


def test_reference_aids_preserve_empty_annotations_and_source_hash(tmp_path, monkeypatch):
    from engine.validation import aids
    import cv2
    import numpy as np
    video = tmp_path / 'source.mp4'
    video.write_bytes(b'fake source for decoder fixture')
    root = tmp_path / 'bundle'
    dataset.prepare([video], root)
    before = (root / 'references/clip-001.json').read_bytes()
    class Capture:
        def __init__(self): self.index = 0
        def get(self, key): return 24.0
        def read(self):
            self.index += 1
            return (True, np.zeros((40, 60, 3), dtype=np.uint8)) if self.index <= 4 else (False, None)
        def release(self): pass
    monkeypatch.setattr(aids.cv2, 'VideoCapture', lambda _: Capture())
    page = aids.prepare_aids(root)
    frames = dataset.read_json(page.parent / 'frames.json')
    assert frames[0]['count'] == 4
    assert frames[0]['reference_positions'] == []
    assert len(list(page.parent.glob('clip-001/*.jpg'))) == 4
    assert (root / 'references/clip-001.json').read_bytes() == before
    assert 'no model landmarks' in page.read_text()
