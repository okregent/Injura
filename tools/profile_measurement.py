"""Local original-frame point annotation; exported profiles remain unreviewed."""

import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import cv2

from engine.validation.dataset import read_json, sha256, write_new
from engine.squat.profile import BodyProfile, ProjectedLength


PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Projected body measurement</title>
<style>body{font:16px system-ui;max-width:1100px;margin:24px auto;line-height:1.6}canvas{max-width:100%;height:auto;display:block;cursor:crosshair}input,select,button{padding:8px;margin:5px}pre{white-space:pre-wrap}label{display:inline-block}</style>
<h1>Projected body measurement</h1>
<p>Mark the same body side in an upright frame. Image distances are not bone lengths. This tool never approves capture conditions or coaching.</p>
<p id="source"></p>
<label>Side <select id="side"><option value="">Select</option><option>left</option><option>right</option></select></label>
<label>View <select id="view"><option value="">Select</option><option>front</option><option>side</option></select></label>
<label>Profile ID <input id="profile" value="draft"></label>
<p>Select a landmark, then click the image. Reclick to correct it.</p>
<select id="landmark"><option>shoulder</option><option>hip</option><option>knee</option><option>ankle</option></select>
<button id="reset">Reset points</button><canvas id="frame"></canvas>
<p>Enter conservative segment-length uncertainty in original-image pixels. Blank is unknown. Bounds do not cover perspective bias.</p>
<label>Torso <input id="torso" type="number" min="0" step="any"></label>
<label>Thigh <input id="thigh" type="number" min="0" step="any"></label>
<label>Shank <input id="shank" type="number" min="0" step="any"></label>
<p id="message" role="status"></p><button id="export" disabled>Download unreviewed profile + point evidence</button>
<pre id="preview"></pre>
<p>The download is a package, not a replacement profile file. Use the import command to verify it and create a new profile JSON. Review flags and reviewer remain unset.</p>
<script>
const source = __SOURCE__;
const names = ['shoulder','hip','knee','ankle'];
let points = {};
const el = id => document.getElementById(id);
const canvas = el('frame'), ctx = canvas.getContext('2d'), img = new Image();
el('source').textContent = 'Original source frame ' + source.frame + ' · ' + source.sha256;
function packageDraft() {
 if (!el('side').value || !el('view').value || !el('profile').value.trim() || names.some(name => !points[name])) return null;
 const segments = {torso:['shoulder','hip'],thigh:['hip','knee'],shank:['knee','ankle']};
 const lengths = {};
 for (const [name,[a,b]] of Object.entries(segments)) {
  const pixels = Math.hypot(points[a].x-points[b].x, points[a].y-points[b].y);
  const text = el(name).value, uncertainty = Number(text);
  if (text.trim()==='' || !Number.isFinite(uncertainty) || uncertainty < 0 || uncertainty >= pixels) return null;
  lengths[name] = {pixels, uncertainty_pixels:uncertainty};
 }
 return {schema_version:1, source_sha256:source.sha256, source_frame:source.frame,
  image_size:source.image_size, points, profile:{schema_version:1,profile_id:el('profile').value.trim(),
  source_sha256:source.sha256,source_frame:source.frame,side:el('side').value,view:el('view').value,
  ...lengths,reviewer:null,upright:null,camera_level:null,joints_visible:null,body_aligned:null}};
}
function update() {
 const draft = packageDraft();
 el('export').disabled = !draft;
 el('message').textContent = draft ? 'Draft ready to download. Independent capture review is still required.' : 'Select side/view, mark all four points and enter valid uncertainty for each segment.';
 el('preview').textContent = draft ? JSON.stringify(draft.profile,null,2) : '';
}
function draw() {
 ctx.clearRect(0,0,canvas.width,canvas.height); ctx.drawImage(img,0,0);
 ctx.fillStyle='#ffdc00'; ctx.strokeStyle='#ffdc00'; ctx.font='16px sans-serif';
 for (const [name,p] of Object.entries(points)) {ctx.beginPath();ctx.arc(p.x,p.y,5,0,2*Math.PI);ctx.fill();ctx.fillText(name,p.x+8,p.y);}
 update();
}
img.onload = () => {canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;draw();};
img.onerror = () => {el('message').textContent='Frame image could not be loaded.';el('export').disabled=true;};
img.src='frame.png';
canvas.onclick = event => {
 if (!img.naturalWidth) return;
 const rect=canvas.getBoundingClientRect();
 const x=(event.clientX-rect.left)*canvas.width/rect.width, y=(event.clientY-rect.top)*canvas.height/rect.height;
 if (x<0 || y<0 || x>=canvas.width || y>=canvas.height) return;
 const selected=el('landmark').value;points[selected]={x,y};
 el('landmark').value=names[Math.min(names.indexOf(selected)+1,names.length-1)];draw();
};
el('reset').onclick=()=>{points={};el('landmark').value=names[0];draw();};
for (const id of ['side','view','profile','torso','thigh','shank']) el(id).oninput=update;
el('export').onclick=()=>{
 const draft=packageDraft();if (!draft) return;
 const url=URL.createObjectURL(new Blob([JSON.stringify(draft,null,2)],{type:'application/json'}));
 const link=document.createElement('a');link.href=url;link.download='profile-measurement-draft.json';link.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
};
</script></html>'''


def export_frame(video, number):
    capture = cv2.VideoCapture(str(video))
    try:
        for _ in range(number + 1):
            ok, frame = capture.read()
            if not ok:
                raise ValueError('source frame cannot be decoded')
        return frame
    finally:
        capture.release()


def measurement_aid(root, frame_number=0):
    root = Path(root)
    if type(frame_number) is not int or frame_number < 0:
        raise ValueError('nonnegative source frame required')
    manifest = read_json(root / 'manifest.json')
    video = Path(manifest['profile_video'])
    digest = sha256(video)
    if digest != manifest['profile_source_sha256']:
        raise ValueError('profile source content changed')
    frame = export_frame(video, frame_number)
    if sha256(video) != digest:
        raise ValueError('source changed during frame export')
    output = root / ('measurement-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(exist_ok=False)
    if not cv2.imwrite(str(output / 'frame.png'), frame):
        raise ValueError('frame could not be saved')
    source = dict(sha256=digest, frame=frame_number, image_size=[frame.shape[1], frame.shape[0]])
    write_new(output / 'source.json', source)
    (output / 'index.html').write_text(PAGE.replace('__SOURCE__', json.dumps(source)), encoding='utf-8')
    return output / 'index.html'


def import_measurement(root, draft_path):
    root = Path(root)
    manifest_digest = sha256(root / 'manifest.json')
    manifest = read_json(root / 'manifest.json')
    draft = read_json(draft_path)
    if draft.get('schema_version') != 1 or type(draft.get('source_frame')) is not int or draft['source_frame'] < 0:
        raise ValueError('unsupported measurement package/frame')
    digest = sha256(manifest['profile_video'])
    if digest != manifest['profile_source_sha256'] or draft['source_sha256'] != digest:
        raise ValueError('measurement source content mismatch')
    frame = export_frame(manifest['profile_video'], draft['source_frame'])
    width, height = frame.shape[1], frame.shape[0]
    if draft['image_size'] != [width, height]:
        raise ValueError('measurement image dimensions mismatch')
    points = draft['points']
    if set(points) != {'shoulder', 'hip', 'knee', 'ankle'}:
        raise ValueError('four landmark points required')
    for point in points.values():
        if set(point) != {'x', 'y'} or any(type(point[key]) not in (int, float) or not math.isfinite(point[key]) for key in ('x', 'y')):
            raise ValueError('finite image coordinates required')
        if not 0 <= point['x'] < width or not 0 <= point['y'] < height:
            raise ValueError('point outside original image')
    data = dict(draft['profile'])
    if data.get('source_frame') != draft['source_frame'] or data.get('source_sha256') != digest:
        raise ValueError('profile/package source disagreement')
    for name, a, b in [('torso', 'shoulder', 'hip'), ('thigh', 'hip', 'knee'), ('shank', 'knee', 'ankle')]:
        distance = math.hypot(points[a]['x'] - points[b]['x'], points[a]['y'] - points[b]['y'])
        segment = ProjectedLength(**data[name])
        if not math.isclose(segment.pixels, distance, rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError('segment length differs from point evidence')
        data[name] = segment
    data.update(reviewer=None, upright=None, camera_level=None, joints_visible=None, body_aligned=None)
    profile = BodyProfile(**data)
    if sha256(manifest['profile_video']) != digest:
        raise ValueError('source changed during import')
    if sha256(root / 'manifest.json') != manifest_digest:
        raise ValueError('setup changed during import')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root / ('profile-measured-' + stamp + '.json')
    write_new(output, asdict(profile))
    write_new(root / ('point-evidence-' + stamp + '.json'), draft)
    write_new(root / ('manifest-before-measurement-' + stamp + '.json'), manifest)
    manifest['profile_file'] = output.name
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return output
