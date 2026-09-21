const $=id=>document.getElementById(id);
const API_BASE = localStorage.getItem('forge_api_base') || '';

const file=$('file'), pick=$('pick'), drop=$('drop'), preview=$('preview'), empty=$('empty'), canvas=$('canvas'), maskCanvas=$('maskCanvas');
const ctx=maskCanvas.getContext('2d'); let currentFile=null, maskMode=false, drawing=false, history=[], historyIndex=-1;

pick.onclick=()=>file.click(); file.onchange=()=>loadFile(file.files[0]);
['dragover','drop'].forEach(e=>drop.addEventListener(e,ev=>ev.preventDefault())); drop.ondrop=e=>loadFile(e.dataTransfer.files[0]);
function loadFile(f){ if(!f||!f.type.startsWith('image/')) return; currentFile=f; const u=URL.createObjectURL(f); preview.src=u; preview.onload=()=>{empty.classList.add('hidden'); $('size').textContent=`${preview.naturalWidth} × ${preview.naturalHeight}`; syncMaskCanvas(); saveState();}; }
function syncMaskCanvas(){ const r=canvas.getBoundingClientRect(); maskCanvas.width=r.width*devicePixelRatio; maskCanvas.height=r.height*devicePixelRatio; maskCanvas.style.width=r.width+'px'; maskCanvas.style.height=r.height+'px'; ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0); ctx.clearRect(0,0,r.width,r.height); }
window.addEventListener('resize',()=>{if(preview.src)syncMaskCanvas()});

function pointerPos(e){const r=maskCanvas.getBoundingClientRect(); return {x:e.clientX-r.left,y:e.clientY-r.top};}
function draw(e){if(!drawing||!maskMode)return; const p=pointerPos(e), size=+$('brush').value; ctx.fillStyle='rgba(145,104,255,.48)'; ctx.beginPath();ctx.arc(p.x,p.y,size/2,0,Math.PI*2);ctx.fill();}
maskCanvas.onpointerdown=e=>{if(!maskMode)return; drawing=true;maskCanvas.setPointerCapture(e.pointerId);draw(e)}; maskCanvas.onpointermove=draw; maskCanvas.onpointerup=()=>{drawing=false;saveState()};
$('maskBtn').onclick=()=>{maskMode=!maskMode; canvas.classList.toggle('masking',maskMode); $('maskState').textContent=maskMode?'Maske çiziliyor':'Maske kapalı';};
$('clearMask').onclick=()=>{const r=canvas.getBoundingClientRect();ctx.clearRect(0,0,r.width,r.height);$('status').textContent='Maske temizlendi.'};
$('brush').oninput=()=>$('brushOut').textContent=$('brush').value+' px'; $('intensity').oninput=()=>$('intensityOut').textContent=$('intensity').value+'%'; $('steps').oninput=()=>$('stepsOut').textContent=$('steps').value; $('guidance').oninput=()=>$('guidanceOut').textContent=$('guidance').value;
function syncEngine(){const ai=$('engine').value==='ai';document.querySelectorAll('.aiOnly').forEach(x=>x.style.display=ai?'block':'none');$('generateText').textContent=ai?'Gerçek AI':'Yerel işlem';} $('engine').onchange=syncEngine; syncEngine();

document.querySelectorAll('.tool').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tool').forEach(x=>x.classList.remove('active'));b.classList.add('active'); $('status').textContent=`Mod: ${b.querySelector('span').textContent}`;});
document.querySelectorAll('.chips button').forEach(b=>b.onclick=()=>{$('prompt').value=b.dataset.prompt});
$('newProject').onclick=()=>location.reload();

// Mobile PWA: prevent accidental page scrolling while drawing the mask.
maskCanvas.style.touchAction='none';
maskCanvas.addEventListener('touchstart',e=>{if(maskMode)e.preventDefault()},{passive:false});
maskCanvas.addEventListener('touchmove',e=>{if(maskMode)e.preventDefault()},{passive:false});

function maskData(){ const temp=document.createElement('canvas'); temp.width=maskCanvas.width;temp.height=maskCanvas.height;const t=temp.getContext('2d');t.drawImage(maskCanvas,0,0); return temp.toDataURL('image/png'); }
async function generate(){
 if(!currentFile){$('status').textContent='Önce bir görsel yükleyin.';return}
 const mode=document.querySelector('.tool.active').dataset.mode; $('generate').disabled=true; $('status').textContent='Yerel prototip işliyor…';
 const fd=new FormData();fd.append('file',currentFile);fd.append('prompt',$('prompt').value);fd.append('mode',mode);fd.append('mask',maskData());fd.append('intensity',+$('intensity').value/100);fd.append('output_ratio',$('ratio').value);
 try{const res=await fetch(API_BASE+'/api/generate',{method:'POST',body:fd});const j=await res.json();if(!res.ok)throw Error(j.detail||'Hata');$('resultImg').src=j.url;$('resultCard').classList.remove('hidden');$('status').textContent='Sonuç hazır ('+(j.engine||'local')+').';}catch(e){$('status').textContent='Hata: '+e.message}finally{$('generate').disabled=false}
}
$('generate').onclick=generate;
$('useResult').onclick=()=>{preview.src=$('resultImg').src;preview.onload=()=>{currentFile=null;$('status').textContent='Sonuç çalışma alanına alındı.'}};
$('exportBtn').onclick=()=>{const src=$('resultImg').src||preview.src;if(!src){$('status').textContent='Önce sonuç üretin.';return}const a=document.createElement('a');a.href=src;a.download='forge-ai-result.png';a.click()};

function saveState(){history=history.slice(0,historyIndex+1);history.push(ctx.getImageData(0,0,maskCanvas.width,maskCanvas.height));historyIndex=history.length-1;if(history.length>20)history.shift()}
$('undo').onclick=()=>{if(historyIndex>0){historyIndex--;ctx.putImageData(history[historyIndex],0,0)}}; $('redo').onclick=()=>{if(historyIndex<history.length-1){historyIndex++;ctx.putImageData(history[historyIndex],0,0)}};
