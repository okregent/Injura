"""Build an exact decoded-source-frame annotation page; never label predictions."""

import json
import os
from pathlib import Path

import cv2


def prepare(root=Path("artifacts/sample-review")):
    output = root / "boundary-review"
    output.mkdir(parents=True, exist_ok=True)
    recordings = []
    for number in (3, 4, 5, 6):
        source = Path(f"sample_video{number}.mp4").resolve()
        metadata = json.loads((root / source.stem / "analysis.json").read_text(encoding="utf-8"))
        signature = f"{source.stat().st_size}-{source.stat().st_mtime_ns}"
        folder = output / f"{source.stem}-{signature}"
        folder.mkdir(exist_ok=True)
        cap = cv2.VideoCapture(str(source))
        count = 0
        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break
                path = folder / f"{count:05d}.jpg"
                if not path.exists():
                    if not cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85]):
                        raise OSError(path)
                count += 1
        finally:
            cap.release()
        if count != metadata["source_frames"]:
            raise ValueError(f"Source frame count changed for {source.name}; regenerate analysis")
        recordings.append({"video": source.name, "frames": count, "fps": metadata["fps"],
                           "folder": folder.name, "signature": signature,
                           "original": Path(os.path.relpath(source, output)).as_posix()})
    page = PAGE.replace("__RECORDINGS__", json.dumps(recordings).replace("<", "\\u003c"))
    (output / "index.html").write_text(page, encoding="utf-8")
    print(output.resolve() / "index.html")


PAGE = r'''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Source-frame boundary review</title>
<style>body{font:16px system-ui;margin:24px;line-height:1.5}img{max-height:65vh;max-width:100%}button,input,select{font:inherit;margin:4px}table{border-collapse:collapse}td,th{padding:7px;border:1px solid #ccd}#seek{width:min(800px,90vw)}.note{background:#fff2cf;padding:12px}</style>
<h1>Source-frame boundary review</h1>
<p class="note">Review labels are entered by you. No detector boundaries are prefilled.
Exclude initial/final partial movements and preparation. Start = departure from standing;
bottom = deepest physical posture; end = return to standing. If unclear, leave a boundary blank
and explain in notes. Images are decoded source frames (zero-based), not estimated video-player times.</p>
<p><a href="../model-comparison/batch-comparison.html">Model comparison</a> |
<a href="../boundary-annotations.csv">Existing annotation CSV (never overwritten)</a></p>
<label>Video <select id="video"></select></label><a id="original">Open original video</a><br>
<button id="prev">−1 frame</button><button id="next">+1 frame</button>
<input id="frame" type="number" min="0" value="0"><span id="position"></span><br>
<input id="seek" type="range" min="0" value="0"><br><img id="image" alt="Decoded source frame"><br>
<button data-mark="start_source">Mark start</button><button data-mark="bottom_source">Mark bottom</button>
<button data-mark="end_source">Mark end</button><button id="clear">Clear marks</button><p id="marks"></p>
<label>Reviewer <input id="reviewer"></label><label>Notes <input id="notes" size="45"></label>
<button id="add">Add reviewed row</button><button id="export">Export CSV (all videos)</button>
<p id="status" role="status"></p><table><thead><tr><th>Video</th><th>Rep</th><th>Start</th><th>Bottom</th><th>End</th><th>Reviewer</th><th>Notes</th><th></th></tr></thead><tbody id="rows"></tbody></table>
<p>Rows are saved in this browser when available. Export CSV to retain a portable copy;
merge it with existing annotations after review. Neither the existing CSV nor detector results are modified.
Keyboard arrows step frames when focus is outside input fields. Display seconds assume constant FPS.</p>
<script>
const recordings=__RECORDINGS__;
const $=id=>document.getElementById(id), keys=['start_source','bottom_source','end_source'];
const storageKey='injura-boundaries-v1-'+recordings.map(r=>r.signature).join(':');
let rows=[],marks={},index=0;
try {rows=JSON.parse(localStorage.getItem(storageKey)||'[]');if(!Array.isArray(rows))rows=[];}catch(e){rows=[];}
recordings.forEach((r,i)=>{const o=document.createElement('option');o.value=i;o.textContent=r.video;$('video').append(o);});
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(rows));}catch(e){$('status').textContent='Browser storage unavailable. Export CSV before closing.';}}
function render(){const r=recordings[index],f=Math.max(0,Math.min(r.frames-1,Math.round(Number($('frame').value)||0)));
 $('frame').value=f;$('seek').value=f;$('frame').max=$('seek').max=r.frames-1;
 $('image').src=r.folder+'/'+String(f).padStart(5,'0')+'.jpg';
 $('position').textContent=` / ${r.frames-1} · ${(f/r.fps).toFixed(3)} seconds`;
 $('original').href=r.original;$('marks').textContent=keys.map(k=>k+': '+(marks[k]??'blank')).join(' | ');}
function table(){ $('rows').replaceChildren(); rows.forEach((row,i)=>{const tr=document.createElement('tr');
 ['video','actual_rep_id',...keys,'reviewer','notes'].forEach(k=>{const td=document.createElement('td');td.textContent=row[k]??'';tr.append(td);});
 const td=document.createElement('td'),b=document.createElement('button');b.textContent='Delete';b.onclick=()=>{rows.splice(i,1);persist();table();};td.append(b);tr.append(td);$('rows').append(tr);});}
$('video').onchange=()=>{index=Number($('video').value);marks={};$('frame').value=0;render();};
$('frame').oninput=render;$('seek').oninput=()=>{$('frame').value=$('seek').value;render();};
function step(n){$('frame').value=Number($('frame').value)+n;render();}
$('prev').onclick=()=>step(-1);$('next').onclick=()=>step(1);
document.onkeydown=e=>{if(['INPUT','SELECT','TEXTAREA','BUTTON'].includes(e.target.tagName))return;
 if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();step(e.key==='ArrowLeft'?-1:1);}};
document.querySelectorAll('[data-mark]').forEach(b=>b.onclick=()=>{marks[b.dataset.mark]=Number($('frame').value);render();});
$('clear').onclick=()=>{marks={};render();};
$('add').onclick=()=>{const reviewer=$('reviewer').value.trim(),notes=$('notes').value.trim(),present=keys.filter(k=>marks[k]!=null);
 if(!reviewer||!present.length){$('status').textContent='Enter a reviewer and at least one boundary.';return;}
 if(present.length<3&&!notes){$('status').textContent='Explain uncertain/missing boundaries in notes.';return;}
 if(present.some((k,i)=>i&&marks[present[i-1]]>=marks[k])){$('status').textContent='Boundaries must satisfy start < bottom < end.';return;}
 const video=recordings[index].video,ids=rows.filter(r=>r.video===video).map(r=>Number(r.actual_rep_id)||0);
 rows.push({video,actual_rep_id:Math.max(0,...ids)+1,...marks,reviewer,notes});persist();table();marks={};render();$('status').textContent='Reviewed row added. Export CSV to retain a copy.';};
function csvCell(v){return '"'+String(v??'').replaceAll('"','""')+'"';}
$('export').onclick=()=>{if(!rows.length){$('status').textContent='No reviewed rows to export.';return;}
 const columns=['video','actual_rep_id',...keys,'reviewer','notes'];
 const csv='\ufeff'+[columns.map(csvCell).join(','),...rows.map(r=>columns.map(k=>csvCell(r[k])).join(','))].join('\r\n');
 const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');
 a.href=url;a.download='boundary-annotations-reviewed.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
table();render();
</script></html>'''


if __name__ == "__main__":
    prepare()
