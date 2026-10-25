const diaryBrowsers={private:{mode:'list',place:null,month:null,day:null},public:{mode:'list',place:null,month:null,day:null}};
function memoryPostCount(n){return n+' '+(n===1?'publicação':'publicações')}
function memoryDay(value){const day=String(value||'').slice(0,10);return /^\d{4}-\d{2}-\d{2}$/.test(day)?day:''}
function memoryPlaceKey(e){return String(e.trip_id||'')+':'+String(e.place||'Local não informado').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').trim().replace(/\s+/g,' ')}
function groupMemoryPlaces(entries){const map=new Map();for(const e of entries){const key=memoryPlaceKey(e);if(!map.has(key))map.set(key,{key,label:e.place||'Local não informado',entries:[]});map.get(key).entries.push(e)}return [...map.values()].sort((a,b)=>a.label.localeCompare(b.label,'pt-BR'))}
function memoryMonthCells(year,month){const first=new Date(year,month,1),offset=(first.getDay()+6)%7,count=new Date(year,month+1,0).getDate();return Array.from({length:Math.ceil((offset+count)/7)*7},(_,i)=>{const day=i-offset+1;return day>0&&day<=count?`${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`:null})}
function memoryViewerButtons(e){return `<div class="memory-view-buttons"><button type="button" data-memory-slides="${e.id}">▧ Ver slides</button><button type="button" data-memory-clip="${e.id}">▷ Ver miniclipe</button></div>`}
function memoryGallery(e,editable=false){return `<div class="memory-thumbnail-grid">${(e.files||[]).map(f=>{const video=f.mime.startsWith('video/'),visual=video||f.mime.startsWith('image/');return `<div class="memory-thumbnail-item">${visual?`<button type="button" class="memory-thumbnail" data-memory-thumbnail="${e.id}" data-memory-file="${f.id}" aria-label="${video?'Reproduzir vídeo':'Abrir foto'}: ${esc(f.name)}">${video?`<video src="/media/${f.id}#t=0.1" preload="metadata" muted playsinline tabindex="-1" aria-hidden="true"></video><span class="memory-video-badge">▷ Vídeo</span>`:`<img src="/media/${f.id}" alt="${esc(f.name)}" loading="lazy">`}</button>`:media(f)}${editable?`<button type="button" class="text-btn danger" data-del-file="${f.id}">Remover arquivo</button>`:''}</div>`}).join('')}</div>`}
function memoryModeToolbar(scope){const current=diaryBrowsers[scope].mode;return `<div class="memory-modes" role="group" aria-label="Visualização das memórias">${[['list','▧ Memórias'],['places','⌖ Por local'],['calendar','▦ Calendário']].map(([mode,label])=>`<button type="button" data-diary-mode="${mode}" data-diary-scope="${scope}" aria-pressed="${current===mode}">${label}</button>`).join('')}</div>`}
function setMemoryMode(scope,mode){diaryBrowsers[scope].mode=mode;diaryBrowsers[scope].place=null;diaryBrowsers[scope].day=null;redrawMemoryBrowser(scope)}
function redrawMemoryBrowser(scope){if(scope==='public')renderPublicPosts();else renderResults()}
function renderMemoryBrowser(entries,scope,renderPosts){
  const ui=diaryBrowsers[scope];let html=memoryModeToolbar(scope);
  if(ui.mode==='list')return html+renderPosts(entries);
  if(ui.mode==='places'){
    const groups=groupMemoryPlaces(entries),selected=groups.find(g=>g.key===ui.place);
    if(selected)return html+`<div class="memory-section-heading"><button class="text-btn" data-place-back="${scope}">← Todos os locais</button><h2>${esc(selected.label)}</h2><span>${memoryPostCount(selected.entries.length)}</span><div><button class="text-btn" data-place-slides="${scope}">▧ Slides do local</button><button class="text-btn" data-place-clip="${scope}">▷ Miniclipe do local</button></div></div>`+renderPosts(selected.entries);
    return html+`<div class="memory-place-grid">${groups.map((g,i)=>{const image=g.entries.flatMap(e=>e.files||[]).find(f=>f.mime.startsWith('image/'));return `<button type="button" class="memory-place-card" data-place-index="${i}" data-diary-scope="${scope}">${image?`<img src="/media/${image.id}" alt="${esc(g.label)}" loading="lazy">`:'<span class="memory-place-placeholder">⌖</span>'}<span class="memory-place-copy"><strong>${esc(g.label)}</strong><small>${memoryPostCount(g.entries.length)} · ${g.entries.reduce((n,e)=>n+(e.files||[]).filter(f=>/^(image|video)\//.test(f.mime)).length,0)} fotos/vídeos</small></span></button>`}).join('')}</div>`;
  }
  const days=new Map();for(const e of entries){const day=memoryDay(e.start);if(day){if(!days.has(day))days.set(day,[]);days.get(day).push(e)}}
  const latest=[...days.keys()].sort().at(-1)||memoryToday();
  if(!ui.month)ui.month=latest.slice(0,7);
  const [year,monthNumber]=ui.month.split('-').map(Number),month=monthNumber-1;
  const currentDays=[...days.keys()].filter(d=>d.startsWith(ui.month));
  if(ui.day&&ui.day!=='undated'&&!currentDays.includes(ui.day))ui.day=null;
  if(ui.day===null)ui.day=currentDays.sort().at(-1)||'';
  const cells=memoryMonthCells(year,month);
  const selected=ui.day==='undated'?entries.filter(e=>!memoryDay(e.start)):days.get(ui.day)||[];
  html+=`<section class="memory-calendar" aria-label="Calendário de publicações"><div class="calendar-heading"><button type="button" data-calendar-shift="-1" data-diary-scope="${scope}" aria-label="Mês anterior">←</button><h2>${new Date(year,month,1).toLocaleDateString('pt-BR',{month:'long',year:'numeric'})}</h2><button type="button" data-calendar-shift="1" data-diary-scope="${scope}" aria-label="Próximo mês">→</button></div><div class="calendar-weekdays">${['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'].map(d=>`<span>${d}</span>`).join('')}</div><div class="calendar-days">${cells.map(day=>{if(!day)return '<span class="calendar-blank"></span>';const count=days.get(day)?.length||0;return count?`<button type="button" class="calendar-post-day" data-calendar-day="${day}" data-diary-scope="${scope}" aria-pressed="${ui.day===day}" aria-label="${day.split('-').reverse().join('/')}: ${memoryPostCount(count)}"><strong>${Number(day.slice(-2))}</strong><span aria-hidden="true">▧</span><small>${count}</small></button>`:`<span class="calendar-empty-day">${Number(day.slice(-2))}</span>`}).join('')}</div><p class="calendar-legend">▧ Clique nas datas marcadas para ver as publicações.</p>${entries.some(e=>!memoryDay(e.start))?`<button type="button" class="text-btn" data-calendar-day="undated" data-diary-scope="${scope}">Ver publicações sem data</button>`:''}</section>`;
  return html+(selected.length?`<div class="memory-section-heading"><h2>${ui.day==='undated'?'Publicações sem data':ui.day.split('-').reverse().join('/')}</h2><span>${memoryPostCount(selected.length)}</span><div><button class="text-btn" data-calendar-slides="${scope}">▧ Slides do dia</button><button class="text-btn" data-calendar-clip="${scope}">▷ Miniclipe do dia</button></div></div>`+renderPosts(selected):'<div class="empty">Não há publicações neste mês. Use as setas para navegar pelo calendário.</div>');
}
function bindMemoryBrowser(entries,scope){
  document.querySelectorAll(`[data-diary-mode][data-diary-scope="${scope}"]`).forEach(b=>b.onclick=()=>setMemoryMode(scope,b.dataset.diaryMode));
  document.querySelectorAll(`[data-place-index][data-diary-scope="${scope}"]`).forEach(b=>b.onclick=()=>{diaryBrowsers[scope].place=groupMemoryPlaces(entries)[Number(b.dataset.placeIndex)].key;redrawMemoryBrowser(scope)});
  document.querySelectorAll(`[data-place-back="${scope}"]`).forEach(b=>b.onclick=()=>{diaryBrowsers[scope].place=null;redrawMemoryBrowser(scope)});
  document.querySelectorAll(`[data-calendar-shift][data-diary-scope="${scope}"]`).forEach(b=>b.onclick=()=>{const ui=diaryBrowsers[scope],[y,m]=ui.month.split('-').map(Number),next=new Date(y,m-1+Number(b.dataset.calendarShift),1);ui.month=`${next.getFullYear()}-${String(next.getMonth()+1).padStart(2,'0')}`;ui.day=null;redrawMemoryBrowser(scope)});
  document.querySelectorAll(`[data-calendar-day][data-diary-scope="${scope}"]`).forEach(b=>b.onclick=()=>{diaryBrowsers[scope].day=b.dataset.calendarDay;redrawMemoryBrowser(scope)});
  const locationRows=()=>entries.filter(e=>memoryPlaceKey(e)===diaryBrowsers[scope].place);
  const dayRows=()=>entries.filter(e=>diaryBrowsers[scope].day==='undated'?!memoryDay(e.start):memoryDay(e.start)===diaryBrowsers[scope].day);
  for(const [type,rows] of [['place',locationRows],['calendar',dayRows]])for(const [mode,auto] of [['slides',false],['clip',true]])document.querySelectorAll(`[data-${type}-${mode}="${scope}"]`).forEach(b=>b.onclick=()=>presentMemories(rows(),auto));
  bindMemoryViewerButtons(entries);
}
function bindMemoryViewerButtons(entries){
  document.querySelectorAll('[data-memory-thumbnail]').forEach(b=>b.onclick=ev=>{ev.stopPropagation();presentMemories(entries.filter(e=>e.id===Number(b.dataset.memoryThumbnail)),false,Number(b.dataset.memoryFile))});
  document.querySelectorAll('[data-memory-slides]').forEach(b=>b.onclick=ev=>{ev.stopPropagation();presentMemories(entries.filter(e=>e.id===Number(b.dataset.memorySlides)),false)});
  document.querySelectorAll('[data-memory-clip]').forEach(b=>b.onclick=ev=>{ev.stopPropagation();presentMemories(entries.filter(e=>e.id===Number(b.dataset.memoryClip)),true)});
}

let memoryFrames=[],memoryFrameIndex=0,memoryPlaying=false,memoryTimer=null,memorySequence=0,memoryPhotosOnly=false;
function clearMemoryTimer(){if(memoryTimer!==null)clearTimeout(memoryTimer);memoryTimer=null}
function memoryFramesFor(entries,photosOnly=false){return entries.flatMap(e=>(e.files||[]).filter(f=>photosOnly?f.mime.startsWith('image/'):/^(image|video)\//.test(f.mime)).map(f=>({entry:e,file:f})))}
function presentMemories(entries,auto=false,startFileId=null){
  const frames=memoryFramesFor(entries,auto);if(!frames.length)return toast(auto?'Esta seleção não tem fotos para o miniclipe.':'Esta seleção ainda não tem fotos ou vídeos para apresentar.');
  clearMemoryTimer();memoryFrames=frames;memoryPhotosOnly=auto;memoryFrameIndex=Math.max(0,frames.findIndex(x=>x.file.id===startFileId));memoryPlaying=auto;$('#memoryRepeat').checked=false;$('#memoryViewer').showModal();showMemoryFrame();
}
function updateMemoryPlaybackButton(){$('#memoryPlayPause').textContent=memoryPlaying?'Ⅱ Pausar':!memoryPhotosOnly?'▷ Miniclipe só de fotos':memoryFrameIndex===memoryFrames.length-1?'↻ Reproduzir novamente':'▷ Reproduzir';$('#memoryPlayPause').disabled=!memoryFrames.some(x=>x.file.mime.startsWith('image/'));$('#memoryPlayPause').setAttribute('aria-pressed',String(memoryPlaying))}
function scheduleMemoryFrame(sequence){clearMemoryTimer();if(!memoryPlaying||!$('#memoryViewer').open||sequence!==memorySequence)return;const ms=Number($('#memorySpeed').value)*1000;memoryTimer=setTimeout(()=>advanceMemoryFrame(),ms)}
function advanceMemoryFrame(){
  clearMemoryTimer();
  if(memoryFrameIndex<memoryFrames.length-1){memoryFrameIndex++;showMemoryFrame()}
  else if($('#memoryRepeat').checked){memoryFrameIndex=0;showMemoryFrame()}
  else{memoryPlaying=false;updateMemoryPlaybackButton();$('#memoryViewer').classList.remove('is-playing')}
}
function showMemoryFrame(){
  stopMemoryMedia();
  clearMemoryTimer();const sequence=++memorySequence,{entry:e,file:f}=memoryFrames[memoryFrameIndex],video=f.mime.startsWith('video/');
  $('#memoryViewer').classList.toggle('is-playing',memoryPlaying);
  $('#memoryViewerStage').innerHTML=video?`<video id="memoryFrameMedia" src="/media/${f.id}" controls playsinline preload="metadata" aria-label="${esc(f.name)}"></video>`:`<img id="memoryFrameMedia" src="/media/${f.id}" alt="${esc(f.name)}">`;
  $('#memoryVideoOriginal').hidden=!video;$('#memoryVideoOriginal').href=`/media/${f.id}`;
  $('#memoryFrameTitle').textContent=e.title;$('#memoryFrameCaption').textContent=`${e.place||'Nossa viagem'} · ${date(e.start)} · ${e.author}`;
  $('#memoryFrameCount').textContent=`${memoryFrameIndex+1} / ${memoryFrames.length}`;$('#memoryFramePrev').disabled=memoryFrameIndex===0;$('#memoryFrameNext').disabled=memoryFrameIndex===memoryFrames.length-1;
  $('#memoryFrameProgress').style.width=`${(memoryFrameIndex+1)/memoryFrames.length*100}%`;updateMemoryPlaybackButton();
  const media=$('#memoryFrameMedia');
  media.onerror=()=>{if(sequence!==memorySequence)return;$('#memoryFrameCaption').textContent+=' · Não foi possível carregar este arquivo.';scheduleMemoryFrame(sequence)};
  if(video){memoryPlaying=false;clearMemoryTimer();updateMemoryPlaybackButton();$('#memoryViewer').classList.remove('is-playing')}
  else{media.onload=()=>scheduleMemoryFrame(sequence);if(media.complete)scheduleMemoryFrame(sequence)}
}
function stopMemoryMedia(){const previous=$('#memoryFrameMedia');if(previous?.tagName==='VIDEO'){previous.pause();previous.removeAttribute('src');previous.load()}}
function initMemoryViewer(){
  $('#memoryFramePrev').onclick=()=>{if(memoryFrameIndex>0){memoryFrameIndex--;showMemoryFrame()}};
  $('#memoryFrameNext').onclick=()=>{if(memoryFrameIndex<memoryFrames.length-1){memoryFrameIndex++;showMemoryFrame()}};
  $('#memoryPlayPause').onclick=()=>{if(!memoryPhotosOnly){const current=memoryFrames[memoryFrameIndex]?.file.id;memoryFrames=memoryFrames.filter(x=>x.file.mime.startsWith('image/'));memoryFrameIndex=Math.max(0,memoryFrames.findIndex(x=>x.file.id===current));memoryPhotosOnly=true;if(!memoryFrames.length)return;memoryPlaying=true}else{memoryPlaying=!memoryPlaying;if(memoryPlaying&&memoryFrameIndex===memoryFrames.length-1)memoryFrameIndex=0}showMemoryFrame()};
  $('#memorySpeed').onchange=()=>{if(memoryPlaying&&$('#memoryFrameMedia')?.tagName==='IMG')scheduleMemoryFrame(memorySequence)};
  $('#memoryViewer').addEventListener('close',()=>{memoryPlaying=false;memorySequence++;clearMemoryTimer();stopMemoryMedia();$('#memoryViewerStage').innerHTML='';memoryFrames=[];$('#memoryViewer').classList.remove('is-playing')});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&$('#memoryViewer').open&&memoryPlaying){memoryPlaying=false;clearMemoryTimer();const video=$('#memoryFrameMedia');if(video?.tagName==='VIDEO')video.pause();$('#memoryViewer').classList.remove('is-playing');updateMemoryPlaybackButton()}});
  document.addEventListener('keydown',e=>{if(!$('#memoryViewer').open||['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;if(e.key==='ArrowRight'){$('#memoryFrameNext').click();e.preventDefault()}if(e.key==='ArrowLeft'){$('#memoryFramePrev').click();e.preventDefault()}});
}
