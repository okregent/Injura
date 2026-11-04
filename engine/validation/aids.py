"""Blinded exact-source-frame viewer; no pose predictions or reference labels."""

import json
from pathlib import Path
from datetime import datetime, timezone

import cv2

from engine.validation.dataset import read_json, sha256, local_path, reference_positions, write_new


def prepare_aids(root):
    root = Path(root)
    manifest = read_json(root / 'manifest.json')
    # This writes a new view only, never an annotation/review or existing aid set.
    output = root / 'reference-aids'
    if output.exists():
        output = root / ('reference-aids-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(exist_ok=False)
    recordings = []
    for number, entry in enumerate(manifest['clips'], 1):
        video = Path(entry['video'])
        if sha256(video) != entry['sha256']:
            raise ValueError('source changed before reference preparation')
        folder = output / f'clip-{number:03d}'
        folder.mkdir()
        cap = cv2.VideoCapture(str(video))
        fps, count, original_size = cap.get(cv2.CAP_PROP_FPS), 0, None
        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break
                height, width = frame.shape[:2]
                original_size = [width, height]
                if width > 960:
                    frame = cv2.resize(frame, (960, round(height * 960 / width)))
                if not cv2.imwrite(str(folder / f'{count:06d}.jpg'), frame, [cv2.IMWRITE_JPEG_QUALITY, 90]):
                    raise OSError('could not write source frame')
                count += 1
        finally:
            cap.release()
        if count == 0:
            raise ValueError(f'no decodable frames: {video.name}')
        if sha256(video) != entry['sha256']:
            raise ValueError('source changed while preparing frames')
        reference = read_json(local_path(root, entry['reference']))
        try:
            positions = reference_positions(reference.get('repetitions', []))
        except (KeyError, TypeError, ValueError):
            positions = []
        if any(type(frame) is not int or frame < 0 or frame >= count for frame in positions):
            positions = []
        recordings.append(dict(id=entry['id'], video=video.name, source_sha256=entry['sha256'],
                               count=count, fps=fps, original_size=original_size, folder=folder.name,
                               source_url=video.as_uri(), reference_positions=positions))
    write_new(output / 'frames.json', recordings)
    page = PAGE.replace('__RECORDINGS__', json.dumps(recordings).replace('<', '\\u003c'))
    (output / 'index.html').write_text(page, encoding='utf-8')
    return output / 'index.html'


PAGE = r'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Blind source review</title>
<style>body{font:16px system-ui;margin:24px;line-height:1.6}img{max-width:100%;max-height:75vh}button,input,select{font:inherit;margin:5px}#seek{width:min(900px,95vw)}.note{padding:14px;background:#fff2cf}</style>
<h1>Blind source reference review</h1><p class="note">Original decoded frames only: no model landmarks,
counts or suggested labels. This viewer does not approve capture conditions or confirm reference truth.
Annotations/review JSON files are never edited here. Display images may be resized; source indices are exact.
Player times assume constant cadence and do not verify it.</p>
<select id="clip"></select><a id="source">Original video</a><br>
<button id="prev">Previous frame</button><button id="next">Next frame</button>
<input id="frame" type="number" min="0" value="0"><span id="info"></span><br>
<input id="seek" type="range" min="0" value="0"><div id="positions"></div><img id="image" alt="Original decoded source frame">
<p>Record independently reviewed events/values in the bundle's reference JSON, and capture conditions
in review JSON. Reviewer and independent confirmation remain required. Blank files stay unconfirmed.</p>
<script>
const recordings=__RECORDINGS__, $=id=>document.getElementById(id);let index=0;
for(let i=0;i<recordings.length;i++){const option=document.createElement('option');option.value=i;option.textContent=recordings[i].video;$('clip').append(option);}
function render(){const r=recordings[index],frame=Math.max(0,Math.min(r.count-1,Math.round(Number($('frame').value)||0)));
$('frame').value=$('seek').value=frame;$('frame').max=$('seek').max=r.count-1;
$('image').src=r.folder+'/'+String(frame).padStart(6,'0')+'.jpg';$('source').href=r.source_url;
$('info').textContent=' / '+(r.count-1)+' source frames · original '+r.original_size.join('×');}
function step(n){$('frame').value=Number($('frame').value)+n;render();}
$('prev').onclick=()=>step(-1);$('next').onclick=()=>step(1);$('frame').oninput=render;
$('seek').oninput=()=>{$('frame').value=$('seek').value;render();};
$('clip').onchange=()=>{index=Number($('clip').value);$('frame').value=0;$('positions').replaceChildren();
for(const frame of recordings[index].reference_positions){const b=document.createElement('button');b.textContent='Reference position '+frame;b.onclick=()=>{$('frame').value=frame;render();};$('positions').append(b);}render();};
document.onkeydown=e=>{if(['INPUT','SELECT','BUTTON'].includes(e.target.tagName))return;
if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();step(e.key==='ArrowLeft'?-1:1);}};
$('clip').onchange();
</script></html>'''
