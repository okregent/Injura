import json
import shutil
import subprocess

import numpy as np
import pytest

from engine.validation.dataset import read_json, sha256
from tools import profile_measurement as measurement
from tests.test_personal_setup import bundle


@pytest.fixture
def draft(bundle, monkeypatch):
    monkeypatch.setattr(measurement, 'export_frame', lambda *args: np.zeros((100, 200, 3), dtype=np.uint8))
    digest = read_json(bundle / 'manifest.json')['profile_source_sha256']
    profile = dict(schema_version=1, profile_id='manual', source_sha256=digest, source_frame=0,
        side='left', view='front', reviewer='must be cleared', upright=True, camera_level=True,
        joints_visible=True, body_aligned=True,
        **{name: dict(pixels=20, uncertainty_pixels=1) for name in ('torso', 'thigh', 'shank')})
    value = dict(schema_version=1, source_sha256=digest, source_frame=0, image_size=[200, 100], profile=profile,
                 points={name: dict(x=50, y=y) for name, y in zip(('shoulder', 'hip', 'knee', 'ankle'), (10, 30, 50, 70))})
    path = bundle / 'download.json'
    path.write_text(json.dumps(value), encoding='utf-8')
    return bundle, path


def test_import_preserves_original_and_clears_all_review(draft):
    root, path = draft
    before = (root / 'profile.json').read_bytes()
    result = measurement.import_measurement(root, path)
    data = read_json(result)
    assert data['reviewer'] is None and data['upright'] is None
    assert (root / 'profile.json').read_bytes() == before
    assert read_json(root / 'manifest.json')['profile_file'] == result.name
    assert len(list(root.glob('point-evidence-*.json'))) == 1
    assert len(list(root.glob('manifest-before-measurement-*.json'))) == 1


@pytest.mark.parametrize('change', ['length', 'bounds', 'dimensions', 'hash', 'nonfinite'])
def test_invalid_measurement_package_rejected_before_output(draft, change):
    root, path = draft
    value = read_json(path)
    if change == 'length':
        value['profile']['torso']['pixels'] = 21
    elif change == 'bounds':
        value['points']['shoulder']['x'] = 500
    elif change == 'dimensions':
        value['image_size'] = [100, 200]
    elif change == 'hash':
        value['source_sha256'] = 'f' * 64
    else:
        value['points']['shoulder']['x'] = float('nan')
    path.write_text(json.dumps(value), encoding='utf-8')
    with pytest.raises(ValueError):
        measurement.import_measurement(root, path)
    assert not list(root.glob('profile-measured-*.json'))


def test_aid_uses_original_dimensions_and_preserves_profile(draft):
    root, _ = draft
    before = sha256(root / 'profile.json')
    page = measurement.measurement_aid(root, 0)
    assert read_json(page.parent / 'source.json')['image_size'] == [200, 100]
    assert (page.parent / 'frame.png').is_file()
    assert sha256(root / 'profile.json') == before
    assert measurement.measurement_aid(root, 0) != page


def test_scaled_canvas_coordinates_and_export_guards(tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for browser-logic verification')
    source = dict(sha256='a' * 64, frame=0, image_size=[200, 100])
    script = measurement.PAGE.replace('__SOURCE__', json.dumps(source)).split('<script>')[1].split('</script>')[0]
    harness = '''
const assert=require('assert');
const elements={};
const drawing={clearRect(){},drawImage(){},beginPath(){},arc(){},fill(){},fillText(){}};
global.document={getElementById(id){return elements[id] ||= {value:'',textContent:'',disabled:false,
 getContext(){return drawing},getBoundingClientRect(){return {left:10,top:20,width:100,height:50}}};}};
global.Image=class {constructor(){this.naturalWidth=200;this.naturalHeight=100}set src(value){this.onload()}};
'''
    assertions = '''
el('side').value='left';el('view').value='front';el('profile').value='manual';el('landmark').value='shoulder';
for(const y of [25,35,45,55]) canvas.onclick({clientX:35,clientY:y});
assert.deepStrictEqual(points.shoulder,{x:50,y:10});
assert.strictEqual(packageDraft(),null);
for(const name of ['torso','thigh','shank']) el(name).value='1';
const result=packageDraft();assert.strictEqual(result.profile.torso.pixels,20);
assert.strictEqual(result.profile.reviewer,null);assert.strictEqual(result.profile.upright,null);
el('reset').onclick();assert.strictEqual(packageDraft(),null);
'''
    path = tmp_path / 'verify.cjs'
    path.write_text(harness + script + assertions, encoding='utf-8')
    result = subprocess.run([node, str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
