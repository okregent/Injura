const el=id=>document.getElementById(id);
let capabilities=null,previewUrl=null,result=null;
let overlayFrames=new Map();
function statusTitle(status){return ({capture_review:'Recording review required',measurement_review:'Measurement review required',retake:'Record again',observation:'Observation only',no_complete_cycles:'No complete cycles detected',not_requested:'not requested',not_validated:'not validated',pending_validation:'pending validation',partial_comparison:'partial comparison',descriptive_comparison:'descriptive comparison',context_mismatch:'recording or profile context differs',comparison_unavailable:'comparison unavailable',no_observations:'no observations'})[status]||status;}
function metricTitle(card){
 const names={'timing:total_seconds':'Total cycle time','timing:descent_seconds':'Descent time','timing:bottom_seconds':'Bottom phase time','timing:ascent_seconds':'Ascent time','knee_flexion:':'Knee flexion','hip_flexion:':'Hip flexion','torso_lean:max_lean_angle':'Maximum torso lean','torso_lean:lean_change':'Torso lean change','depth:depth_ratio':'Relative descent'};
 return names[card.metric+':'+(card.field||'')]||card.metric;
}
function reasonTitle(value){
 const fields={side_view:'side view',camera_fixed:'fixed camera',subject_clear:'unobstructed person',hips_visible:'hips visible',knees_visible:'knees visible',ankles_visible:'ankles visible',shoulders_visible:'shoulders visible',feet_visible:'feet visible',foot_side_on:'foot seen from the side',continuous_original_speed:'continuous original-speed footage',constant_frame_rate:'constant frame rate'};
 const reasons={recording_review_missing:'This recording has not been reviewed.',recording_reviewer_missing:'A named recording reviewer is required.',recording_review_side_mismatch:'The recording review belongs to a different body side.'};
 let reason=reasons[value]||value||'';
 for(const [prefix,label] of [['recording_review_unknown:','Confirm capture condition: '],['recording_review_rejected:','Capture condition not met: ']])if(reason.startsWith(prefix)){const field=reason.slice(prefix.length);reason=label+(fields[field]||field)+'.';}
 return reason;
}
function measurementValue(card){return Number.isFinite(card.observation)?new Intl.NumberFormat('en',{maximumFractionDigits:2}).format(card.observation)+' '+({degrees:'°',seconds:'s'}[card.unit]||card.unit):'Not shown';}
function formatCard(card){return metricTitle(card)+' · '+statusTitle(card.status)+' · '+measurementValue(card)+' · '+reasonTitle(card.reason)+(card.action?' · '+card.action:'');}
function renderSelectedCards(cards){
 const groups=new Map();
 for(const card of cards){const key=JSON.stringify([card.status,card.reason,card.action]);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(card);}
 for(const group of groups.values()){
  const first=group[0],row=document.createElement('li'),metrics=document.createElement('ul');
  row.textContent=statusTitle(first.status)+' · '+reasonTitle(first.reason)+(first.action?' · '+first.action:'');
  for(const card of group){const item=document.createElement('li');item.textContent=metricTitle(card)+' · '+measurementValue(card);metrics.append(item);}
  row.append(metrics);el('selected-evidence').append(row);
 }
}
function invalidate(){result=null;overlayFrames=new Map();el('overlay-toggle').checked=false;el('overlay-toggle').disabled=true;drawOverlay();el('result').hidden=true;el('selected').hidden=true;el('selected-evidence-panel').hidden=true;el('seek-status').textContent='';el('status').textContent='';}
function setBusy(busy){for(const id of ['video','side','facing','submit','result-file'])el(id).disabled=busy;el('load-result').disabled=busy||!el('result-file').files?.length;}
function parseSavedResult(text){
 const data=JSON.parse(text.charCodeAt(0)===0xfeff?text.slice(1):text);
 const pending=[[data,0]];let visited=0;
 while(pending.length){
  const [value,depth]=pending.pop();if(++visited>200000 || depth>32)throw Error('Saved result is too complex.');
  if(typeof value==='number' && !Number.isFinite(value))throw Error('Saved result contains invalid numbers.');
  if(value && typeof value==='object')for(const child of Object.values(value))pending.push([child,depth+1]);
 }
 const fail=()=>{throw Error('Unsupported or inconsistent saved result.');};
 const integer=value=>Number.isInteger(value)&&value>=0;
 if(!data || data.schema_version!==1 || data.exercise!=='squat' || !data.source || !data.selection || !data.overview || !data.feedback || !data.interpretation)fail();
 const source=data.source,overview=data.overview,feedback=data.feedback;
 if(!/^[a-f0-9]{64}$/.test(source.sha256) || !integer(source.frame_count) || !integer(source.pose_frame_count) || source.pose_frame_count>source.frame_count || !(source.fps===null || (Number.isFinite(source.fps)&&source.fps>0)))fail();
 if(!['left','right'].includes(data.selection.side) || !['left','right'].includes(data.selection.facing))fail();
 if(!Array.isArray(data.repetitions) || !Array.isArray(data.candidates) || !Array.isArray(feedback.cards) || !Array.isArray(feedback.actions) || !Array.isArray(feedback.notices))fail();
 if(overview.detected_cycles!==data.repetitions.length || overview.excluded_candidates!==data.candidates.length)fail();
 if(overview.accuracy_status!=='not_validated' || overview.coaching_status!=='pending_validation' || data.interpretation.accuracy!=='not_validated' || data.interpretation.coaching!=='pending_validation')throw Error('This viewer does not accept saved accuracy/coaching approvals.');
 if(!['retake','capture_review','measurement_review','observation','no_complete_cycles'].includes(overview.state) || typeof overview.primary_action!=='string' || !['not_requested','no_observations','comparison_unavailable','context_mismatch','partial_comparison','descriptive_comparison'].includes(overview.personal_comparison_state))fail();
 const validFrame=frame=>integer(frame)&&frame<source.frame_count;
 const bounds=item=>item && item.source_frames && validFrame(item.source_frames.start) && validFrame(item.source_frames.end) && item.source_frames.start<=item.source_frames.end;
 data.repetitions.forEach((item,index)=>{if(!bounds(item) || item.number!==index+1 || !validFrame(item.source_frames.bottom_phase_end) || item.source_frames.bottom_phase_end<item.source_frames.start || item.source_frames.bottom_phase_end>item.source_frames.end)fail();});
 for(const item of data.candidates)if(!bounds(item) || !validFrame(item.observed_bottom) || item.observed_bottom<item.source_frames.start || item.observed_bottom>item.source_frames.end || typeof item.reason!=='string')fail();
 const cardKeys=new Set();
 for(const card of feedback.cards){
  if(!Number.isInteger(card.repetition) || card.repetition<1 || card.repetition>data.repetitions.length || typeof card.metric!=='string' || !(card.field===null||typeof card.field==='string') || typeof card.unit!=='string' || !(card.reason===null||typeof card.reason==='string') || typeof card.action!=='string' || !['retake','capture_review','measurement_review','observation'].includes(card.status) || !(card.observation===null || Number.isFinite(card.observation)) || (card.coaching_status!==undefined&&card.coaching_status!=='pending_validation'))fail();
  if((card.status==='observation')!==Number.isFinite(card.observation))fail();
  const key=JSON.stringify([card.repetition,card.metric,card.field]);if(cardKeys.has(key))fail();cardKeys.add(key);
 }
 for(const action of feedback.actions)if(typeof action.action!=='string' || !Array.isArray(action.repetitions) || action.repetitions.some(number=>!Number.isInteger(number)||number<1||number>data.repetitions.length))fail();
 for(const notice of feedback.notices)if(typeof notice.message!=='string')fail();
 if(data.overlay){
  const overlay=data.overlay;
  if(overlay.schema_version!==1 || overlay.side!==data.selection.side || !Array.isArray(overlay.frames) || overlay.frames.length!==source.pose_frame_count || !Array.isArray(overlay.image_size) || overlay.image_size.length!==2 || !overlay.image_size.every(value=>Number.isInteger(value)&&value>0))fail();
  let previous=-1;
  for(const frame of overlay.frames){
   if(!validFrame(frame.source_frame) || frame.source_frame<=previous || !['observed','recovered_not_shown'].includes(frame.status) || !frame.points)fail();previous=frame.source_frame;
   for(const [name,point] of Object.entries(frame.points)){if(!['shoulder','hip','knee','ankle','heel','toe'].includes(name))fail();if(point!==null&&(!point || !Number.isFinite(point.x)||!Number.isFinite(point.y)||point.x<0||point.x>1||point.y<0||point.y>1))fail();}
  }
 }
 return data;
}
async function reopenSavedResult(videoFile,resultFile){
 if(!videoFile || !resultFile)throw Error('Select the original video and a saved result JSON.');
 if(resultFile.size>4*1024*1024)throw Error('Saved result exceeds the 4 MiB limit.');
 if(videoFile.size>(capabilities?.limits.file_bytes||25*1024*1024))throw Error('Video exceeds the supported file size.');
 const data=parseSavedResult(await resultFile.text());
 const digest=await crypto.subtle.digest('SHA-256',await videoFile.arrayBuffer());
 const hash=Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,'0')).join('');
 if(hash!==data.source.sha256)throw Error('The selected video does not match the saved result source hash.');
 return data;
}
function drawOverlay(){
 const canvas=el('pose-overlay'),video=el('preview');
 if(!canvas.getContext)return;
 const ctx=canvas.getContext('2d');if(!ctx)return;
 ctx.clearRect(0,0,canvas.width,canvas.height);canvas.hidden=true;
 const note=message=>{el('overlay-note').textContent=message;};
 if(!result || !result.overlay || !el('overlay-toggle').checked){note('Overlay is off. Selected-side image coordinates are not anatomical accuracy or posture approval.');return;}
 if(!video.paused || video.seeking){note('Pause the video after seeking to inspect joints. No overlay is interpolated during playback.');return;}
 const source=result.source,overlay=result.overlay;
 if(!source || !Number.isFinite(source.fps) || source.fps<=0 || !Number.isFinite(video.currentTime)){note('Overlay timing is unavailable without valid FPS.');return;}
 if(!result.selection || overlay.side!==result.selection.side){note('Overlay body side does not match the selected analysis.');return;}
 const size=overlay.image_size;
 if(!Array.isArray(size) || size.length!==2 || !size.every(value=>Number.isInteger(value)&&value>0) || video.videoWidth!==size[0] || video.videoHeight!==size[1]){note('Video dimensions differ or metadata is not ready; overlay is hidden.');return;}
 const scaled=video.currentTime*source.fps,nearest=Math.round(scaled);
 const index=Math.abs(scaled-nearest)<.001?nearest:Math.floor(scaled),frame=overlayFrames.get(index);
 if(frameTime(result,index)===null || !frame || frame.status!=='observed'){note('No original pose observation for approximate source frame '+index+'. Gaps and recovered observations are not drawn.');return;}
 canvas.width=size[0];canvas.height=size[1];canvas.style.width=video.clientWidth+'px';canvas.style.height=video.clientHeight+'px';
 const visible={};
 for(const name of ['shoulder','hip','knee','ankle','heel','toe']){const point=frame.points[name];if(point && Number.isFinite(point.x) && Number.isFinite(point.y) && point.x>=0 && point.x<=1 && point.y>=0 && point.y<=1)visible[name]=point;}
 ctx.strokeStyle='#7cddff';ctx.fillStyle='#7cddff';ctx.lineWidth=Math.max(2,canvas.width/400);
 for(const [a,b] of [['shoulder','hip'],['hip','knee'],['knee','ankle'],['ankle','heel'],['heel','toe'],['ankle','toe']]){if(!visible[a] || !visible[b])continue;ctx.beginPath();ctx.moveTo(visible[a].x*canvas.width,visible[a].y*canvas.height);ctx.lineTo(visible[b].x*canvas.width,visible[b].y*canvas.height);ctx.stroke();}
 for(const point of Object.values(visible)){ctx.beginPath();ctx.arc(point.x*canvas.width,point.y*canvas.height,Math.max(3,canvas.width/200),0,Math.PI*2);ctx.fill();}
 canvas.hidden=!Object.keys(visible).length;
 note(canvas.hidden?'No selected-side joints meet the display visibility/bounds checks.':'Approximate source frame '+index+' · selected-side joints only. Reported-FPS timing and browser seeking are not frame-exact; visibility is not accuracy.');
}
function frameTime(data,frame){
 const source=data.source;
 return source && Number.isFinite(source.fps) && source.fps>0 && Number.isInteger(frame) && frame>=0 && Number.isInteger(source.frame_count) && frame<source.frame_count ? frame/source.fps : null;
}
function seekFrame(data,frame){
 if(result!==data)return false;
 const seconds=frameTime(data,frame),video=el('preview');
 if(seconds===null){el('seek-status').textContent='Time navigation is unavailable: valid FPS and source-frame information are required.';return false;}
 if(video.readyState<1 || !Number.isFinite(video.duration) || video.duration<=0){el('seek-status').textContent='Video metadata is not ready. Try again after the local preview loads.';return false;}
 if(seconds>=video.duration){el('seek-status').textContent='The reported frame position falls outside the browser video duration; inspect the source manually.';return false;}
 try{video.pause();video.currentTime=seconds;el('seek-status').textContent='Approximate source frame '+frame+' · '+seconds.toFixed(3)+' s using reported FPS. Browser seeking is not frame-exact.';return true;}
 catch(error){el('seek-status').textContent='This video cannot seek to the requested position in the browser.';return false;}
}
function selectCycle(data,item,candidate=false,index=0){
 if(result!==data)return;
 el('selected').hidden=false;el('seek-controls').replaceChildren();el('selected-evidence').replaceChildren();
 el('selected-title').textContent=candidate?'Review candidate '+(index+1)+' · not a measured repetition':'Detected cycle '+item.number;
 el('selected-evidence-panel').hidden=false;el('evidence-title').textContent=el('selected-title').textContent+' · evidence';
 const items=candidate?data.candidates:data.repetitions;
 el('previous-cycle').disabled=index<=0;el('next-cycle').disabled=index>=items.length-1;
 el('previous-cycle').onclick=()=>{if(index>0)selectCycle(data,items[index-1],candidate,index-1);};
 el('next-cycle').onclick=()=>{if(index+1<items.length)selectCycle(data,items[index+1],candidate,index+1);};
 const frames=item.source_frames;
 el('selected-frames').textContent='Original source frames '+frames.start+'–'+frames.end+'.'+(candidate?' '+item.reason:' Bottom phase end is not necessarily the deepest posture.');
 const controls=candidate?[['Start',frames.start],['Observed bottom',item.observed_bottom],['End',frames.end]]:[['Start',frames.start],['Bottom phase end',frames.bottom_phase_end],['End',frames.end]];
 for(const [label,frame] of controls){const button=document.createElement('button');button.type='button';button.textContent=label+' · frame '+frame;button.disabled=frameTime(data,frame)===null;button.onclick=()=>seekFrame(data,frame);el('seek-controls').append(button);}
 const cards=candidate?[]:data.feedback.cards.filter(card=>card.repetition===item.number);
 renderSelectedCards(cards);
 if(!cards.length){const row=document.createElement('li');row.textContent=candidate?'No measurements or phase times are assigned to review candidates.':'No measurement cards are available for this detected cycle.';el('selected-evidence').append(row);}
 seekFrame(data,frames.start);
 if(typeof window!=='undefined' && window.matchMedia('(max-width:899px)').matches && el('media-panel').scrollIntoView)el('media-panel').scrollIntoView({behavior:'smooth',block:'start'});
}
function renderNavigator(data){
 el('cycles').replaceChildren();el('candidates').replaceChildren();el('selected').hidden=true;el('selected-evidence-panel').hidden=true;
 el('timing-note').textContent=frameTime(data,0)===null?'FPS/source-frame information is unavailable. You can inspect evidence, but time navigation is disabled.':'Navigation uses original frame numbers divided by reported FPS. It is approximate, especially for variable-rate or edited video; no frame-exact boundary accuracy is implied.';
 for(const [candidate,items,target] of [[false,data.repetitions||[],'cycles'],[true,data.candidates||[],'candidates']]){
  items.forEach((item,index)=>{const row=document.createElement('li'),button=document.createElement('button');button.type='button';button.textContent=candidate?'Review candidate '+(index+1):'Detected cycle '+item.number;button.onclick=()=>selectCycle(data,item,candidate,index);row.append(button);el(target).append(row);});
  if(!items.length){const row=document.createElement('li');row.textContent=candidate?'No excluded candidates.':'No complete detected cycles. Review the source and gap evidence.';el(target).append(row);}
 }
}
function showResult(data,saved=false){
 const overview=data.overview;
 el('summary').textContent=statusTitle(overview.state)+' · '+overview.primary_action;
 el('counts').textContent='Detected cycles: '+overview.detected_cycles+' · Excluded candidates: '+overview.excluded_candidates+' · Personal comparison: '+statusTitle(overview.personal_comparison_state);
 el('validation').textContent='Measurement accuracy: '+statusTitle(overview.accuracy_status)+' · Coaching: '+statusTitle(overview.coaching_status);
 el('result-origin').textContent=saved?'Saved result: unverified file contents. The video hash matches, but no new analysis or independent approval was performed.':'Fresh analysis from this local server. Measurement and coaching validation remain pending.';
 el('actions').replaceChildren();el('cards').replaceChildren();
 for(const action of data.feedback.actions){const item=document.createElement('li');item.textContent=action.action+' · Repetitions '+action.repetitions.join(', ');el('actions').append(item);}
 for(const notice of data.feedback.notices){const item=document.createElement('li');item.textContent=notice.message;el('actions').append(item);}
 for(const card of data.feedback.cards){const item=document.createElement('li');item.textContent='Cycle '+card.repetition+' · '+formatCard(card);el('cards').append(item);}
 el('json').textContent=JSON.stringify(data,null,2);el('result').hidden=false;result=data;renderNavigator(data);
 overlayFrames=new Map((data.overlay?data.overlay.frames:[]).map(frame=>[frame.source_frame,frame]));
 el('overlay-toggle').checked=false;el('overlay-toggle').disabled=!data.overlay;drawOverlay();
}
el('overlay-toggle').onchange=drawOverlay;
for(const event of ['onpause','onplay','onseeking','onseeked','ontimeupdate','onloadedmetadata','onresize','onerror'])el('preview')[event]=drawOverlay;
if(typeof ResizeObserver!=='undefined')new ResizeObserver(drawOverlay).observe(el('preview'));
el('video').onchange=()=>{
 invalidate();
 if(previewUrl)URL.revokeObjectURL(previewUrl);
 const file=el('video').files[0];el('preview').hidden=!file;
 el('media-panel').hidden=!file;
 el('side').value='';el('facing').value='';
 if(file)el('status').textContent='Select the body side and facing for this recording, or reopen a matching saved result.';
 if(file){previewUrl=URL.createObjectURL(file);el('preview').src=previewUrl;}
};
el('side').onchange=invalidate;el('facing').onchange=invalidate;
el('result-file').onchange=()=>{el('load-result').disabled=!el('result-file').files?.length;};
el('load-result').onclick=async()=>{
 const videoFile=el('video').files?.[0],resultFile=el('result-file').files?.[0];
 setBusy(true);invalidate();el('status').textContent='Checking saved result and original video…';
 try{
  const data=await reopenSavedResult(videoFile,resultFile);
  if(el('video').files[0]!==videoFile)throw Error('Video selection changed during verification.');
  el('side').value=data.selection.side;el('facing').value=data.selection.facing;
  showResult(data,true);el('status').textContent='Reopened a matching saved file locally. It has not been re-analyzed or approved.';
 }catch(error){el('status').textContent=error.message||'Could not reopen the saved result.';}
 finally{setBusy(false);}
};
el('upload').onsubmit=async event=>{
 event.preventDefault();if(!capabilities)return;
 const file=el('video').files[0];
 if(!file || !['left','right'].includes(el('side').value) || !['left','right'].includes(el('facing').value)){el('status').textContent='Select a video, body side and facing direction.';return;}
 if(file.size>capabilities.limits.file_bytes){el('status').textContent='Video exceeds the supported file size.';return;}
 setBusy(true);invalidate();el('status').textContent='Analyzing… Please keep this page open.';
 const form=new FormData();form.append('video',file);form.append('side',el('side').value);form.append('facing',el('facing').value);
 try{const response=await fetch('/v1/analyses',{method:'POST',body:form});const data=await response.json();
  if(!response.ok){el('status').textContent=data.error?data.error.message+' ('+data.error.code+')':'The request failed.';return;}
  if(data.schema_version!==1 || data.exercise!=='squat')throw Error('unsupported response');
  showResult(data);el('status').textContent='Analysis complete. Review measurement limits and capture conditions.';
 }catch(error){el('status').textContent='Could not complete the request. Check the local server and try again.';}
 finally{setBusy(false);}
};
el('download').onclick=()=>{
 if(!result)return;const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));
 const link=document.createElement('a');link.href=url;link.download='injura-analysis.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
fetch('/v1/capabilities').then(response=>{if(!response.ok)throw Error();return response.json();}).then(data=>{
 capabilities=data;el('limits').textContent='Maximum '+Math.floor(data.limits.file_bytes/1024/1024)+' MiB · '+data.limits.frames+' decoded frames · '+data.limits.width+' × '+data.limits.height+' pixels.';el('submit').disabled=false;
}).catch(()=>{el('limits').textContent='Could not load server capabilities. Start the local server and reload.';});
