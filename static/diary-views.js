// Endereço da mídia: com largura, a versão leve (WebP) preparada pelo servidor; sem, o original.
function mediaUrl(f,w){return `/media/${f.id}?${w&&/^image\/(jpeg|png|webp|heic|heif)$/.test(f.mime)?'w='+w+'&':''}v=${f.v||''}`}
// src + srcset: o navegador escolhe 480, 1280 ou 1920 px conforme tela e densidade.
function imgAttrs(f,sizes){return /^image\/(jpeg|png|webp|heic|heif)$/.test(f.mime)?`src="${mediaUrl(f,1280)}" srcset="${mediaUrl(f,480)} 480w, ${mediaUrl(f,1280)} 1280w, ${mediaUrl(f,1920)} 1920w" sizes="${sizes}"`:`src="${mediaUrl(f)}"`}
// Capa escolhida pelo autor (cover_file_id); sem escolha, vale a primeira foto da ordem definida.
function coverOf(entries){const list=[].concat(entries);for(const e of list){const c=(e.files||[]).find(f=>f.id===e.cover_file_id&&f.mime.startsWith('image/'));if(c)return c}return list.flatMap(e=>e.files||[]).find(f=>f.mime.startsWith('image/'))}
const diaryBrowsers={private:{mode:'list',place:null,month:null,day:null},public:{mode:'list',place:null,month:null,day:null}};
function memoryPostCount(n){return n+' '+(n===1?'publicação':'publicações')}
function memoryDay(value){const day=String(value||'').slice(0,10);return /^\d{4}-\d{2}-\d{2}$/.test(day)?day:''}
function memoryPlaceKey(e){return String(e.trip_id||'')+':'+String(e.place||'Local não informado').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').trim().replace(/\s+/g,' ')}
function groupMemoryPlaces(entries){const map=new Map();for(const e of entries){const key=memoryPlaceKey(e);if(!map.has(key))map.set(key,{key,label:e.place||'Local não informado',entries:[]});map.get(key).entries.push(e)}return [...map.values()].sort((a,b)=>a.label.localeCompare(b.label,'pt-BR'))}
function memoryMonthCells(year,month){const first=new Date(year,month,1),offset=(first.getDay()+6)%7,count=new Date(year,month+1,0).getDate();return Array.from({length:Math.ceil((offset+count)/7)*7},(_,i)=>{const day=i-offset+1;return day>0&&day<=count?`${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`:null})}
function memoryViewerButtons(e){return `<div class="memory-view-buttons"><button type="button" data-memory-slides="${e.id}">▧ Ver slides</button><button type="button" data-memory-clip="${e.id}">▷ Ver miniclipe</button></div>`}
function memoryGallery(e,editable=false){
  const files=e.files||[],cover=coverOf(e);
  return `<div class="memory-thumbnail-grid${editable?' is-arranging':''}"${editable?' data-arrange-grid':''}>${files.map((f,i)=>{const video=f.mime.startsWith('video/'),visual=video||f.mime.startsWith('image/'),isCover=cover?.id===f.id;
    const dl=editable?`<a class="photo-download" href="/media/${f.id}?download=1" download title="Baixar ${video?'o clipe':'a foto'} no tamanho original" aria-label="Baixar original: ${esc(f.name)}">⬇</a>`:'';
    const adm=editable&&isAdminUser()?`<button type="button" class="photo-admin" data-photo-admin="${f.id}" title="Editar: mover, excluir, capa, ponto de interesse" aria-label="Editar ${esc(f.name)}">✎</button>`:'';
    const tools=editable?`<div class="photo-tools" role="group" aria-label="Organizar ${esc(f.name)}"><button type="button" data-file-move="${f.id}" data-dir="-1" ${i===0?'disabled':''} aria-label="Mover para antes" title="Mover para antes">‹</button>${f.mime.startsWith('image/')?`<button type="button" data-file-cover="${f.id}" ${isCover?'disabled':''} title="Usar como foto de capa">${isCover?'★ Capa':'☆ Capa'}</button>`:''}<button type="button" data-file-move="${f.id}" data-dir="1" ${i===files.length-1?'disabled':''} aria-label="Mover para depois" title="Mover para depois">›</button></div>`:'';
    return `<div class="memory-thumbnail-item${isCover?' is-cover':''}" data-file-item="${f.id}"${editable?' draggable="true"':''}>${visual?`<button type="button" class="memory-thumbnail" data-memory-thumbnail="${e.id}" data-memory-file="${f.id}" aria-label="${video?'Reproduzir vídeo':'Abrir foto'}: ${esc(f.name)}">${video?`<video src="${mediaUrl(f)}#t=0.1" preload="metadata" muted playsinline tabindex="-1" aria-hidden="true"></video><span class="memory-video-badge">▷ Vídeo</span>`:`<img src="${mediaUrl(f,480)}" alt="${esc(f.name)}" loading="lazy" draggable="false">`}${isCover?'<span class="memory-cover-badge">★ Capa</span>':''}</button>`:media(f)}${dl}${adm}${tools}${editable?`<button type="button" class="text-btn danger" data-del-file="${f.id}">Remover arquivo</button>`:''}</div>`}).join('')}</div>${editable&&files.length>1?'<p class="photo-arrange-hint">Arraste as miniaturas ou use ‹ › para mudar a ordem; ☆ Capa define a foto de destaque da memória.</p>':''}`}
// Ordem e capa: salva no servidor e reabre o detalhe mantendo a rolagem.
function bindFileArranging(e){
  const grid=document.querySelector('[data-arrange-grid]');if(!grid)return;
  const ids=()=>(e.files||[]).map(f=>f.id);
  let busy=false,dragged=null;
  async function save(body){
    if(busy)return;busy=true;const box=$('#detail'),top=box.scrollTop;
    try{await api('/api/files/arrange',{entry_id:e.id,...body});await load();detail(e.id);box.scrollTop=top}
    catch(ex){toast(ex.message);busy=false}
  }
  function moved(list,id,target,after){if(id===target)return list;const rest=list.filter(x=>x!==id);rest.splice(rest.indexOf(target)+(after?1:0),0,id);return rest}
  grid.querySelectorAll('[data-file-move]').forEach(b=>b.onclick=()=>{const list=ids(),id=Number(b.dataset.fileMove),at=list.indexOf(id),to=at+Number(b.dataset.dir);if(to<0||to>=list.length)return;[list[at],list[to]]=[list[to],list[at]];save({file_ids:list})});
  grid.querySelectorAll('[data-photo-admin]').forEach(b=>b.onclick=()=>{const file=(e.files||[]).find(f=>f.id===Number(b.dataset.photoAdmin));if(file)openPhotoAdmin(e,file,async()=>{await load();detail(e.id)})});
  grid.querySelectorAll('[data-file-cover]').forEach(b=>b.onclick=()=>save({cover_file_id:Number(b.dataset.fileCover)}));
  grid.querySelectorAll('[data-file-item]').forEach(item=>{
    item.ondragstart=ev=>{dragged=Number(item.dataset.fileItem);item.classList.add('is-dragging');ev.dataTransfer.effectAllowed='move';ev.dataTransfer.setData('text/plain',String(dragged))};
    item.ondragend=()=>{dragged=null;grid.querySelectorAll('.drop-before,.drop-after,.is-dragging').forEach(x=>x.classList.remove('drop-before','drop-after','is-dragging'))};
    item.ondragover=ev=>{if(dragged===null)return;ev.preventDefault();const r=item.getBoundingClientRect(),after=ev.clientX>r.left+r.width/2;grid.querySelectorAll('.drop-before,.drop-after').forEach(x=>x.classList.remove('drop-before','drop-after'));if(Number(item.dataset.fileItem)!==dragged)item.classList.add(after?'drop-after':'drop-before')};
    item.ondrop=ev=>{if(dragged===null)return;ev.preventDefault();const r=item.getBoundingClientRect(),list=ids(),result=moved(list,dragged,Number(item.dataset.fileItem),ev.clientX>r.left+r.width/2);dragged=null;if(result.some((id,i)=>id!==list[i]))save({file_ids:result})};
  });
}
function memoryModeToolbar(scope){const current=diaryBrowsers[scope].mode;return `<div class="memory-modes" role="group" aria-label="Visualização das memórias">${[['list','▧ Memórias'],['places','⌖ Por local'],['calendar','▦ Calendário'],...(scope==='private'?[['map','◌ Mapa']]:[])].map(([mode,label])=>`<button type="button" data-diary-mode="${mode}" data-diary-scope="${scope}" aria-pressed="${current===mode}">${label}</button>`).join('')}</div>`}
function setMemoryMode(scope,mode){diaryBrowsers[scope].mode=mode;diaryBrowsers[scope].place=null;diaryBrowsers[scope].day=null;redrawMemoryBrowser(scope)}
function redrawMemoryBrowser(scope){if(scope==='home')return render();if(scope==='public')renderPublicPosts();else renderResults()}
function renderMemoryBrowser(entries,scope,renderPosts,toolbar=true){
  const ui=diaryBrowsers[scope];let html=toolbar?memoryModeToolbar(scope):'';
  if(ui.mode==='list')return html+renderPosts(entries);
  if(ui.mode==='map'&&scope==='private')return html+mapMarkup('private','Mapa mundi da viagem: toque em um ponto para abrir as fotos; ao tocar na viagem, veja o resumo com datas, países e pontos visitados.');
  if(ui.mode==='places'){
    const groups=groupMemoryPlaces(entries),selected=groups.find(g=>g.key===ui.place);
    if(selected)return html+`<div class="memory-section-heading"><button class="text-btn" data-place-back="${scope}">← Todos os locais</button><h2>${esc(selected.label)}</h2><span>${memoryPostCount(selected.entries.length)}</span><div><button class="text-btn" data-place-slides="${scope}">▧ Slides do local</button><button class="text-btn" data-place-clip="${scope}">▷ Miniclipe do local</button></div></div>`+renderPosts(selected.entries);
    return html+`<div class="memory-place-grid">${groups.map((g,i)=>{const image=coverOf(g.entries);return `<button type="button" class="memory-place-card" data-place-index="${i}" data-diary-scope="${scope}">${image?`<img ${imgAttrs(image,'(max-width:700px) 100vw, 34vw')} alt="${esc(g.label)}" loading="lazy">`:'<span class="memory-place-placeholder">⌖</span>'}<span class="memory-place-copy"><strong>${esc(g.label)}</strong><small>${memoryPostCount(g.entries.length)} · ${g.entries.reduce((n,e)=>n+(e.files||[]).filter(f=>/^(image|video)\//.test(f.mime)).length,0)} fotos/vídeos</small></span></button>`}).join('')}</div>`;
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
  if(scope==='private'&&diaryBrowsers.private.mode==='map'){privateMapCtx.posts=entries;initMap(privateMapCtx)}
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
  clearMemoryTimer();memoryFrames=frames;memoryPhotosOnly=auto;memoryFrameIndex=Math.max(0,frames.findIndex(x=>x.file.id===startFileId));memoryPlaying=auto;$('#memoryRepeat').checked=false;setMemoryPanel(false);$('#memoryEditToggle').hidden=!isAdminUser();$('#memoryViewer').showModal();$('#memoryViewerStage').focus?.();showMemoryFrame();
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
  $('#memoryViewerStage').innerHTML=video?`<video id="memoryFrameMedia" src="${mediaUrl(f)}" controls controlsList="nodownload noplaybackrate" disablePictureInPicture playsinline preload="metadata" aria-label="${esc(f.name)}"></video>`:`<img id="memoryFrameMedia" ${imgAttrs(f,'100vw')} alt="${esc(f.name)}">`;
  $('#memoryVideoOriginal').hidden=!video;$('#memoryVideoOriginal').href=mediaUrl(f);
  $('#memoryFrameTitle').textContent=e.title;$('#memoryFrameCaption').textContent=`${e.place||'Nossa viagem'} · ${date(e.start)} · ${e.author}`;
  $('#memoryFrameCount').textContent=$('#memoryFrameCountTop').textContent=`${memoryFrameIndex+1} / ${memoryFrames.length}`;$('#memoryViewer').classList.toggle('at-start',memoryFrameIndex===0);$('#memoryViewer').classList.toggle('at-end',memoryFrameIndex===memoryFrames.length-1);preloadMemoryNeighbors();$('#memoryFramePrev').disabled=memoryFrameIndex===0;$('#memoryFrameNext').disabled=memoryFrameIndex===memoryFrames.length-1;
  $('#memoryFrameProgress').style.width=`${(memoryFrameIndex+1)/memoryFrames.length*100}%`;updateMemoryPlaybackButton();
  const media=$('#memoryFrameMedia');
  media.onerror=()=>{if(sequence!==memorySequence)return;$('#memoryFrameCaption').textContent+=' · Não foi possível carregar este arquivo.';scheduleMemoryFrame(sequence)};
  if(video){memoryPlaying=false;clearMemoryTimer();updateMemoryPlaybackButton();$('#memoryViewer').classList.remove('is-playing')}
  else{media.onload=()=>scheduleMemoryFrame(sequence);if(media.complete)scheduleMemoryFrame(sequence)}
}
// Tela cheia: os controles ficam no painel aberto pelo ☰; troca-se de foto tocando nas bordas ou arrastando.
function setMemoryPanel(open){const panel=$('#memoryViewerPanel');panel.hidden=!open;$('#memoryMenuToggle').setAttribute('aria-expanded',String(open));$('#memoryViewer').classList.toggle('panel-open',open)}
function stepMemoryFrame(delta){const to=memoryFrameIndex+delta;if(to<0||to>=memoryFrames.length)return false;memoryFrameIndex=to;showMemoryFrame();return true}
function preloadMemoryNeighbors(){if(typeof Image==='undefined')return;for(const i of [memoryFrameIndex+1,memoryFrameIndex-1]){const f=memoryFrames[i]?.file;if(!f||!f.mime.startsWith('image/'))continue;const img=new Image();img.sizes='100vw';img.srcset=[480,1280,1920].map(w=>`${mediaUrl(f,w)} ${w}w`).join(', ');img.src=mediaUrl(f,1280)}}
function bindMemoryGestures(){
  const stage=$('#memoryViewerStage');let drag=null;
  const media=()=>$('#memoryFrameMedia');
  stage.addEventListener('pointerdown',e=>{
    if(e.button!==0||!memoryFrames.length)return;
    const r=stage.getBoundingClientRect(),m=media();
    // Vídeo: a faixa inferior pertence aos controles nativos.
    if(m?.tagName==='VIDEO'&&e.clientY>r.bottom-70)return;
    drag={id:e.pointerId,x:e.clientX,y:e.clientY,dx:0,t:Date.now(),video:m?.tagName==='VIDEO'};
  });
  stage.addEventListener('pointermove',e=>{
    if(!drag||e.pointerId!==drag.id||drag.video)return;
    drag.dx=e.clientX-drag.x;
    if(Math.abs(drag.dx)>8){const m=media();if(m){m.style.transition='none';m.style.transform=`translateX(${drag.dx}px)`}}
  });
  const finish=(e,cancel)=>{
    if(!drag||e.pointerId!==drag.id)return;
    const d=drag;drag=null;const m=media(),r=stage.getBoundingClientRect(),dx=e.clientX-d.x,dy=e.clientY-d.y;
    const reset=()=>{if(m){m.style.transition='transform .2s';m.style.transform=''}};
    if(cancel)return reset();
    const fast=Math.abs(dx)>30&&Date.now()-d.t<300;
    if(!d.video&&(Math.abs(dx)>Math.min(90,r.width*.18)||fast)&&Math.abs(dx)>Math.abs(dy)){if(!stepMemoryFrame(dx<0?1:-1))reset();return}
    reset();
    if(Math.abs(dx)<10&&Math.abs(dy)<10){const zone=(e.clientX-r.left)/r.width,edge=d.video?.15:.3;if(zone<edge)stepMemoryFrame(-1);else if(zone>1-edge)stepMemoryFrame(1)}
  };
  stage.addEventListener('pointerup',e=>finish(e,false));
  stage.addEventListener('pointercancel',e=>finish(e,true));
  stage.addEventListener('mousemove',e=>{const r=stage.getBoundingClientRect(),zone=(e.clientX-r.left)/r.width;stage.style.cursor=zone<.3&&memoryFrameIndex>0?'w-resize':zone>.7&&memoryFrameIndex<memoryFrames.length-1?'e-resize':'grab'});
}
// Dissuasão no visualizador: sem menu de contexto, arrastar ou segurar para salvar, e a tela se oculta ao imprimir,
// ao usar PrintScreen ou ao perder o foco. Nenhum site consegue impedir de fato uma captura de tela do aparelho.
function bindMemoryProtection(){
  const viewer=$('#memoryViewer');
  const block=e=>{e.preventDefault()};
  ['contextmenu','dragstart','copy','cut'].forEach(n=>viewer.addEventListener(n,block));
  const hide=on=>viewer.classList.toggle('shielded',on);
  document.addEventListener('keyup',e=>{if(viewer.open&&e.key==='PrintScreen'){hide(true);try{navigator.clipboard?.writeText('')}catch{}setTimeout(()=>hide(false),1500)}});
  document.addEventListener('keydown',e=>{if(viewer.open&&((e.ctrlKey||e.metaKey)&&['s','p','u'].includes(e.key.toLowerCase())||(e.metaKey&&e.shiftKey&&['3','4','5'].includes(e.key))))e.preventDefault()});
  if(typeof window!=='undefined'){window.addEventListener('blur',()=>{if(viewer.open)hide(true)});window.addEventListener('focus',()=>hide(false));window.addEventListener('beforeprint',()=>hide(true));window.addEventListener('afterprint',()=>hide(false))}
}
// Administrador: edita a foto em exibição e, ao concluir, ajusta a sequência sem fechar o visualizador.
function editCurrentMemoryFrame(){
  const frame=memoryFrames[memoryFrameIndex];if(!frame)return;
  memoryPlaying=false;clearMemoryTimer();updateMemoryPlaybackButton();
  openPhotoAdmin(frame.entry,frame.file,async info=>{
    if(info.action==='moved'){frame.entry=info.target}
    else if(info.action==='deleted'){
      memoryFrames.splice(memoryFrameIndex,1);
      if(!memoryFrames.length){$('#memoryViewer').close();load().catch(()=>{});return}
      memoryFrameIndex=Math.min(memoryFrameIndex,memoryFrames.length-1);
    }
    showMemoryFrame();
    try{await load()}catch{}
  });
}
function stopMemoryMedia(){const previous=$('#memoryFrameMedia');if(previous?.tagName==='VIDEO'){previous.pause();previous.removeAttribute('src');previous.load()}}
function initMemoryViewer(){
  $('#memoryFramePrev').onclick=()=>stepMemoryFrame(-1);
  $('#memoryFrameNext').onclick=()=>stepMemoryFrame(1);
  $('#memoryMenuToggle').onclick=()=>setMemoryPanel($('#memoryViewerPanel').hidden);
  $('#memoryEditToggle').onclick=editCurrentMemoryFrame;
  bindMemoryGestures();bindMemoryProtection();
  $('#memoryPlayPause').onclick=()=>{if(!memoryPhotosOnly){const current=memoryFrames[memoryFrameIndex]?.file.id;memoryFrames=memoryFrames.filter(x=>x.file.mime.startsWith('image/'));memoryFrameIndex=Math.max(0,memoryFrames.findIndex(x=>x.file.id===current));memoryPhotosOnly=true;if(!memoryFrames.length)return;memoryPlaying=true}else{memoryPlaying=!memoryPlaying;if(memoryPlaying&&memoryFrameIndex===memoryFrames.length-1)memoryFrameIndex=0}showMemoryFrame()};
  $('#memorySpeed').onchange=()=>{if(memoryPlaying&&$('#memoryFrameMedia')?.tagName==='IMG')scheduleMemoryFrame(memorySequence)};
  $('#memoryViewer').addEventListener('close',()=>{memoryPlaying=false;memorySequence++;clearMemoryTimer();stopMemoryMedia();$('#memoryViewerStage').innerHTML='';memoryFrames=[];$('#memoryViewer').classList.remove('is-playing')});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&$('#memoryViewer').open&&memoryPlaying){memoryPlaying=false;clearMemoryTimer();const video=$('#memoryFrameMedia');if(video?.tagName==='VIDEO')video.pause();$('#memoryViewer').classList.remove('is-playing');updateMemoryPlaybackButton()}});
  document.addEventListener('keydown',e=>{if(!$('#memoryViewer').open||['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;if(e.key==='ArrowRight'){$('#memoryFrameNext').click();e.preventDefault()}if(e.key==='ArrowLeft'){$('#memoryFramePrev').click();e.preventDefault()}});
}
