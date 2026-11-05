import shutil
import subprocess
from pathlib import Path

import pytest


def browser_assertions(tmp_path, assertions):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed to verify preview browser logic')
    page = (Path(__file__).parents[1] / 'apps/api/index.html').read_text(encoding='utf-8')
    script = page.split('<script>')[1].split('</script>')[0]
    harness = '''
const assert=require('assert'),elements={};
function element(){return {value:'',hidden:true,disabled:false,textContent:'',children:[],readyState:1,duration:30,currentTime:0,
 pause(){this.paused=true},replaceChildren(){this.children=[]},append(item){this.children.push(item)}};}
global.document={getElementById(id){return elements[id] ||= element();},createElement:element};
global.fetch=()=>new Promise(()=>{});
const payload={source:{fps:24,frame_count:720},overview:{state:'capture_review',primary_action:'Review capture',detected_cycles:2,
 excluded_candidates:1,personal_comparison_state:'not_requested',accuracy_status:'not_validated',coaching_status:'pending_validation'},
 feedback:{actions:[],notices:[],cards:[{repetition:1,metric:'knee_flexion',field:null,status:'capture_review',observation:null,unit:'degrees',reason:'Review required',action:'Inspect source'},
 {repetition:2,metric:'torso_lean',field:null,status:'capture_review',observation:null,unit:'degrees',reason:'Other cycle',action:'Inspect source'}]},
 repetitions:[{number:1,source_frames:{start:120,bottom_phase_end:144,end:168}},{number:2,source_frames:{start:240,bottom_phase_end:264,end:288}}],
 candidates:[{source_frames:{start:300,end:360},observed_bottom:336,reason:'Gap crossing'}]};
'''
    path = tmp_path / 'navigator.cjs'
    path.write_text(harness + script + assertions, encoding='utf-8')
    result = subprocess.run([node, str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_navigator_uses_source_frames_and_shows_only_selected_cycle_evidence(tmp_path):
    browser_assertions(tmp_path, '''
showResult(payload);assert.strictEqual(el('cycles').children.length,2);
el('cycles').children[0].children[0].onclick();
assert.strictEqual(el('preview').currentTime,5);assert.strictEqual(el('preview').paused,true);
assert.strictEqual(el('selected-evidence').children.length,1);
assert(el('selected-evidence').children[0].textContent.includes('knee_flexion'));
el('seek-controls').children[1].onclick();assert.strictEqual(el('preview').currentTime,6);
assert(el('seek-controls').children[1].textContent.includes('Bottom phase end'));
assert(el('seek-status').textContent.includes('not frame-exact'));
el('cycles').children[1].children[0].onclick();assert.strictEqual(el('preview').currentTime,10);
assert(el('selected-evidence').children[0].textContent.includes('torso_lean'));
''')


def test_candidates_never_borrow_measured_cycle_values(tmp_path):
    browser_assertions(tmp_path, '''
showResult(payload);el('candidates').children[0].children[0].onclick();
assert(el('selected-title').textContent.includes('not a measured repetition'));
assert.strictEqual(el('selected-evidence').children.length,1);
assert(el('selected-evidence').children[0].textContent.includes('No measurements'));
el('seek-controls').children[1].onclick();assert.strictEqual(el('preview').currentTime,14);
''')


@pytest.mark.parametrize('fps', ['null', '0', '-1', 'NaN', 'Infinity'])
def test_unknown_or_invalid_fps_disables_seek_but_preserves_evidence(tmp_path, fps):
    browser_assertions(tmp_path, '''
payload.source.fps=FPS;showResult(payload);el('cycles').children[0].children[0].onclick();
assert(el('timing-note').textContent.includes('disabled'));
assert(el('seek-controls').children.every(button=>button.disabled));
assert.strictEqual(el('preview').currentTime,0);
assert.strictEqual(el('selected-evidence').children.length,1);
'''.replace('FPS', fps))


def test_seek_guards_metadata_duration_indices_and_stale_results(tmp_path):
    browser_assertions(tmp_path, '''
showResult(payload);el('preview').readyState=0;
assert.strictEqual(seekFrame(payload,120),false);assert.strictEqual(el('preview').currentTime,0);
el('preview').readyState=1;el('preview').duration=4;assert.strictEqual(seekFrame(payload,120),false);
el('preview').duration=30;assert.strictEqual(seekFrame(payload,-1),false);
assert.strictEqual(seekFrame(payload,720),false);assert.strictEqual(seekFrame(payload,1.5),false);
const oldButton=el('cycles').children[0].children[0];invalidate();oldButton.onclick();
assert.strictEqual(el('selected').hidden,true);assert.strictEqual(seekFrame(payload,120),false);
''')


def test_empty_cycle_and_candidate_lists_have_explicit_messages(tmp_path):
    browser_assertions(tmp_path, '''
payload.repetitions=[];payload.candidates=[];showResult(payload);
assert(el('cycles').children[0].textContent.includes('No complete'));
assert(el('candidates').children[0].textContent.includes('No excluded'));
''')


OVERLAY_SETUP = '''
const canvas=el('pose-overlay'),video=el('preview'),calls={arcs:[],lines:[]};
canvas.style={};canvas.getContext=()=>({clearRect(){},beginPath(){},moveTo(){},lineTo(x,y){calls.lines.push([x,y])},stroke(){},arc(x,y){calls.arcs.push([x,y])},fill(){}});
video.videoWidth=200;video.videoHeight=100;video.clientWidth=100;video.clientHeight=50;
video.paused=true;video.seeking=false;video.currentTime=5;
payload.selection={side:'left'};
payload.overlay={side:'left',image_size:[200,100],frames:[{source_frame:120,status:'observed',points:{hip:{x:.25,y:.25},knee:{x:.5,y:.5},ankle:null}}]};
showResult(payload);el('overlay-toggle').checked=true;drawOverlay();
'''


def test_paused_overlay_scales_to_video_and_connects_only_visible_neighbors(tmp_path):
    browser_assertions(tmp_path, OVERLAY_SETUP + '''
assert.strictEqual(canvas.hidden,false);assert.strictEqual(canvas.width,200);assert.strictEqual(canvas.height,100);
assert.strictEqual(canvas.style.width,'100px');assert.strictEqual(canvas.style.height,'50px');
assert.deepStrictEqual(calls.arcs,[[50,25],[100,50]]);assert.deepStrictEqual(calls.lines,[[100,50]]);
assert(el('overlay-note').textContent.includes('not frame-exact'));
video.clientWidth=300;video.clientHeight=150;drawOverlay();assert.strictEqual(canvas.style.width,'300px');
''')


def test_overlay_hides_for_gaps_recovery_playback_side_or_dimension_mismatch(tmp_path):
    browser_assertions(tmp_path, OVERLAY_SETUP + '''
video.currentTime=121/24;drawOverlay();assert.strictEqual(canvas.hidden,true);
video.currentTime=5;video.paused=false;drawOverlay();assert.strictEqual(canvas.hidden,true);
video.paused=true;payload.overlay.frames[0].status='recovered_not_shown';drawOverlay();assert.strictEqual(canvas.hidden,true);
payload.overlay.frames[0].status='observed';payload.overlay.side='right';drawOverlay();assert.strictEqual(canvas.hidden,true);
payload.overlay.side='left';video.videoWidth=100;drawOverlay();assert.strictEqual(canvas.hidden,true);
video.videoWidth=200;payload.source.fps=null;drawOverlay();assert.strictEqual(canvas.hidden,true);
''')


def test_overlay_never_clamps_invalid_coordinates_or_reuses_invalidated_results(tmp_path):
    browser_assertions(tmp_path, OVERLAY_SETUP + '''
calls.arcs=[];calls.lines=[];payload.overlay.frames[0].points.knee.x=2;drawOverlay();
assert.deepStrictEqual(calls.arcs,[[50,25]]);assert.strictEqual(calls.lines.length,0);
invalidate();assert.strictEqual(canvas.hidden,true);assert.strictEqual(el('overlay-toggle').disabled,true);
el('overlay-toggle').checked=true;drawOverlay();assert.strictEqual(canvas.hidden,true);
''')


def test_preview_renders_untrusted_text_and_invalidates_stale_selection(tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed to verify preview browser logic')
    page = (Path(__file__).parents[1] / 'apps/api/index.html').read_text(encoding='utf-8')
    script = page.split('<script>')[1].split('</script>')[0]
    harness = '''
const assert=require('assert'),elements={};
global.document={getElementById(id){return elements[id] ||= {value:'',hidden:true,disabled:false,textContent:'',children:[],
 replaceChildren(){this.children=[]},append(item){this.children.push(item)}};},createElement(){return {textContent:''}}};
global.fetch=()=>new Promise(()=>{});
'''
    assertions = '''
const payload={overview:{state:'capture_review',primary_action:'<script>alert(1)</script>',detected_cycles:3,
 excluded_candidates:1,personal_comparison_state:'not_requested',accuracy_status:'not_validated',coaching_status:'pending_validation'},
 feedback:{actions:[{action:'<img src=x>',repetitions:[1]}],notices:[],cards:[]}};
showResult(payload);assert.strictEqual(el('summary').textContent,'capture_review · <script>alert(1)</script>');
assert.strictEqual(el('actions').children[0].textContent,'<img src=x> · Repetitions 1');
assert.strictEqual(result,payload);el('side').onchange();assert.strictEqual(result,null);assert.strictEqual(el('result').hidden,true);
setBusy(true);assert.strictEqual(el('video').disabled,true);assert.strictEqual(el('side').disabled,true);
setBusy(false);assert.strictEqual(el('submit').disabled,false);
'''
    path = tmp_path / 'preview.cjs'
    path.write_text(harness + script + assertions, encoding='utf-8')
    result = subprocess.run([node, str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'innerHTML' not in script
