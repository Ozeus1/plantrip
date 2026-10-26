let attractionData=null,guideDeck=[],guideSlide=0,guideMapSelection=null;
function attractionRoute(){return location.pathname.match(/^\/attractions\/(\d+)\/?$/)?.[1]}
function leaveAttraction(){if(attractionRoute())history.pushState({},'', '/');resetAttractionLayout()}
function resetAttractionLayout(){if('speechSynthesis' in window)speechSynthesis.cancel();document.title='Plantrip — histórias pelo caminho';$('.page').classList.remove('attraction-mode');$('.page-heading').hidden=false;if($('#tripNotice'))$('#tripNotice').hidden=false;attractionData=null}
function photoCredit(p){return `<span>${esc(p.author)} · <a href="${esc(p.license_url)}" target="_blank" rel="noopener">${esc(p.license)}</a> · <a href="${esc(p.source)}" target="_blank" rel="noopener">Original ↗</a></span>`}
function guideDayEntries(day){
  const place=attractionData?.entry.place||'Roma',tripId=attractionData?.entry.trip_id;
  return state.entries.filter(e=>e.kind==='tour'&&memoryDay(e.start)===day&&e.place===place&&(!tripId||e.trip_id===tripId));
}
function guideMapQuery(entry){return entry.guide?.map_query||((attractionData?.entry.id===entry.id&&attractionData?.guide?.map_query)||`${entry.title} ${entry.place}`)}
function guidePlaceMapUrl(entry){return 'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(guideMapQuery(entry))}
function guideDayMapUrl(entries){
  if(!entries.length)return '';
  if(entries.length===1)return guidePlaceMapUrl(entries[0]);
  const params=new URLSearchParams({api:'1',origin:guideMapQuery(entries[0]),destination:guideMapQuery(entries[entries.length-1]),travelmode:'walking'});
  if(entries.length>2)params.set('waypoints',entries.slice(1,-1).map(guideMapQuery).join('|'));
  return 'https://www.google.com/maps/dir/?'+params.toString();
}
function guideMapSegments(entries,maxPoints){
  const segments=[];let start=0;
  while(start<entries.length){
    let end=Math.min(start+maxPoints,entries.length);
    while(end>start+2&&guideDayMapUrl(entries.slice(start,end)).length>2000)end--;
    segments.push({entries:entries.slice(start,end),start});
    if(end===entries.length)break;
    start=end-1;
  }
  return segments;
}
function showGuideMapSegments(entries,maxPoints){
  const dialog=document.createElement('dialog');dialog.className='day-map-dialog';
  dialog.setAttribute('aria-label','Mapa e sequência do dia');
  const segments=guideMapSegments(entries,maxPoints);
  dialog.innerHTML=`<div class="modal-heading"><h2>Mapa do dia · ${fullDate(guideMapSelection.date)}</h2><button type="button" class="close" aria-label="Fechar mapa">×</button></div><p>Abra os trechos na ordem abaixo para percorrer todos os pontos. A última parada de um trecho inicia o próximo.</p><ol>${entries.map(e=>`<li><a href="${esc(guidePlaceMapUrl(e))}" target="_blank" rel="noopener">${esc(e.title)}</a></li>`).join('')}</ol><div class="day-map-segments">${segments.map((segment,i)=>`<a class="map-button" href="${esc(guideDayMapUrl(segment.entries))}" target="_blank" rel="noopener">Trecho ${i+1} · pontos ${segment.start+1} a ${segment.start+segment.entries.length} ↗</a>`).join('')}</div>`;
  dialog.querySelector('.close').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>dialog.remove(),{once:true});document.body.append(dialog);dialog.showModal();
}
function bindGuideDayMap(entry,guide){
  const link=$('#guideMap');
  if(!link)return;
  const days=guide.route_summary||[];
  if(!guideMapSelection)guideMapSelection={mode:'day',date:memoryDay(entry.start),id:entry.id};
  if(!days.some(day=>day.date===guideMapSelection.date))guideMapSelection.mode='place';
  function update(){
    const selection=guideMapSelection,isDay=selection.mode==='day',entries=isDay?guideDayEntries(selection.date):[entry];
    link.textContent=isDay?'⌖ Abrir mapa do dia':'⌖ Abrir mapa da atração';
    link.href=isDay?guideDayMapUrl(entries):guidePlaceMapUrl(entry);
    link.setAttribute('aria-disabled',String(!entries.length));
    link.title=isDay?`${entries.length} pontos na sequência do quadro`:entry.title;
    document.querySelectorAll('[data-map-day]').forEach(card=>card.classList.toggle('current',card.dataset.mapDay===selection.date));
    document.querySelectorAll('[data-select-map-day]').forEach(button=>button.setAttribute('aria-pressed',String(isDay&&button.dataset.selectMapDay===selection.date)));
    document.querySelectorAll('[data-map-place]').forEach(button=>button.classList.toggle('map-place-selected',!isDay&&Number(button.dataset.mapPlace)===entry.id));
    link.onclick=ev=>{
      if(!entries.length){ev.preventDefault();toast('Este dia ainda não tem pontos no roteiro.');return}
      if(!isDay)return;
      const mobile=/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)||(navigator.maxTouchPoints>1&&/Macintosh/i.test(navigator.userAgent));
      const maxPoints=mobile?5:11;
      if(guideMapSegments(entries,maxPoints).length>1){ev.preventDefault();showGuideMapSegments(entries,maxPoints)}
    };
  }
  document.querySelectorAll('[data-map-day]').forEach(card=>card.onclick=ev=>{
    if(ev.target.closest('[data-guide-nav]'))return;
    guideMapSelection={mode:'day',date:card.dataset.mapDay,id:entry.id};update();
  });
  update();
}
function officialLinks(g){return g.sources.map(s=>`<a class="source-link" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)} <span>↗</span></a>`).join('')}
function planningNotes(value){const parts=String(value||'O administrador ainda não adicionou observações para esta etapa.').split('\n\nRegistro anterior do planejamento (substituído pelo roteiro acima):\n');return `<p class="detail-description">${esc(parts.shift())}</p>${parts.length?`<details class="guide-previous-plan"><summary>Consultar histórico do planejamento anterior</summary><p class="detail-description">${esc(parts.join('\n\n'))}</p></details>`:''}`}
function guideAlternatives(g){if(!g.alternatives?.length)return '';return `<section class="guide-section guide-alternatives"><span class="eyebrow">ESCOLHAS PARA O SEU TEMPO</span><h2>O que cabe — e o que fica para outra ocasião</h2><p>${esc(g.alternatives_intro||'Consulte as alternativas antes de alterar o roteiro.')}</p><details><summary>Ver alternativas, restrições e motivos da seleção</summary>${g.alternatives.map(a=>{const entry=state.entries.find(e=>e.kind==='tour'&&e.guide_key===a.guide_key);return `<article><h3>${esc(a.name)}</h3><p>${esc(a.text)}</p>${entry?`<button type="button" class="text-btn" data-guide-nav="${entry.id}">Consultar guia preservado ↗</button>`:''}<a class="source-link" href="${esc(a.url)}" target="_blank" rel="noopener">Conferir referência <span>↗</span></a></article>`}).join('')}</details></section>`}
function romeDayOverview(g){if(!g.route_summary)return '';const routeDay=g.route_day||g.rome_day,routeSequence=g.route_sequence||g.rome_sequence,routeTitle=g.route_title||'Roma em quatro dias';return `<section class="rome-day-overview${g.route_summary.length===2?' route-two-days':''}" aria-label="${esc(routeTitle)}"><div class="guide-section-heading"><div><span class="eyebrow">${esc(routeTitle.toLocaleUpperCase('pt-BR'))}</span><h2>Um percurso por região.</h2></div><span class="tag">Você está no dia ${routeDay} · parada ${routeSequence}</span></div><div class="rome-days-grid">${g.route_summary.map(day=>`<article data-map-day="${esc(day.date)}" class="rome-day${routeDay===day.day?' current':''}"><span class="eyebrow">DIA ${day.day} · ${fullDate(day.date)}</span><h3><button type="button" class="day-map-select" data-select-map-day="${esc(day.date)}" aria-pressed="false">${esc(day.title)}</button></h3><ol>${guideDayEntries(day.date).map(entry=>`<li><button type="button" class="text-btn" data-guide-nav="${entry.id}" data-map-place="${entry.id}">${esc(entry.title)} <small>${time(entry.start)}${entry.end?' – '+time(entry.end):''}</small></button></li>`).join('')}</ol></article>`).join('')}</div><p class="guide-muted">Clique no quadro para selecionar o mapa do dia ou em uma atração para mostrar apenas esse ponto. Sequência sugerida e editável. Ingressos com hora marcada, abertura e percurso acessível precisam ser confirmados. ${esc(g.route_footnote||'Toscana e Trastevere ficam como alternativas sem data.')}</p></section>`}
async function openAttraction(id,push=true,mapMode='day'){
  try{
    const result=await api('/api/attractions/'+id),e=result.entry;
    if(state.trip_id!==e.trip_id){selectedTrip=String(e.trip_id);state=await api('/api/state?trip_id='+selectedTrip);prepareTrips()}
    if(push)history.pushState({},'', '/attractions/'+id);
    if('speechSynthesis' in window)speechSynthesis.cancel();view='tour';attractionData=result;guideMapSelection={mode:mapMode,date:memoryDay(e.start),id:e.id};renderAttraction(result.entry,result.guide);window.scrollTo({top:0,behavior:'instant'});
  }catch(ex){$('.page-heading').hidden=false;$('#content').innerHTML=`<div class="panel"><h2>Não foi possível abrir o passeio</h2><p>${esc(ex.message)}</p><button class="primary" id="guideErrorBack">Voltar ao roteiro</button></div>`;$('#guideErrorBack').onclick=()=>{leaveAttraction();go('tour')}}
}
function renderAttraction(e,g){
  document.title=e.title+' — Plantrip';$('.page').classList.add('attraction-mode');$('.page-heading').hidden=true;if($('#tripNotice'))$('#tripNotice').hidden=true;
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.view==='tour'));
  $('#breadcrumb').textContent='Nossa viagem / Passeios / '+e.title;
  const guide=g||{intro:e.description,kicker:'Uma descoberta do seu roteiro',photos:[],history:[],stops:[],tips:[],sources:[],arrival:e.place,duration:'A definir',booking:'Confira a reserva com o administrador.',accessibility:'Consulte as condições do local antes da visita.',photo_tip:'Compartilhe as suas fotos com o grupo.',reviewed:''};
  const photos=guide.photos||[],cover=photos[0],memories=state.entries.filter(d=>d.kind==='diary'&&(d.attraction_id===e.id||(!d.attraction_id&&d.place===e.title)));
  const next=state.entries.filter(d=>d.kind==='tour'),index=next.findIndex(d=>d.id===e.id);
  $('#content').innerHTML=`<div class="guide-topbar"><button class="text-btn" id="backToTours">← Voltar ao roteiro</button><span>${esc(e.place)} <span class="guide-divider">/</span> GUIA DO PASSEIO</span><button class="text-btn" id="printGuide">Imprimir guia ↗</button></div>
  <section class="guide-hero">${cover?`<img src="${esc(cover.src)}" alt="${esc(cover.alt)}" fetchpriority="high">`:''}<div class="guide-hero-shade"></div><div class="guide-hero-copy"><span class="eyebrow">${esc(guide.kicker)}</span><h1>${esc(e.title)}</h1><p>${esc(guide.intro)}</p><div class="guide-hero-meta"><span>⌖ ${esc(e.place)}</span><span>◷ ${date(e.start)} ${time(e.start)}${time(e.end)?' — '+time(e.end):''}</span><span>◇ ${esc(guide.duration)}</span></div></div>${cover?`<div class="hero-credit">${photoCredit(cover)}</div>`:''}</section>
  <div class="guide-actions"><div><span class="tag">${esc(state.trips.find(t=>t.id===e.trip_id)?.name||'NOSSA VIAGEM')} · GUIA DO PASSEIO</span><p>Conheça o lugar antes de chegar.</p></div><div><button class="primary" id="startGuideShow">▷ Apresentação guiada</button><a id="guideMap" class="map-button" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(guide.map_query||e.title+' '+e.place)}" target="_blank" rel="noopener">⌖ Abrir mapa</a></div></div>
  ${romeDayOverview(guide)}
  <nav class="guide-tabs" aria-label="Seções do guia"><a href="#guide-history">História</a><a href="#guide-route">O que ver</a><a href="#guide-gallery">Fotos</a><a href="#guide-tips">Dicas práticas</a><a href="#guide-community">Nosso grupo</a></nav>
  <div class="guide-columns"><div class="guide-editorial"><section id="guide-history" class="guide-section"><span class="eyebrow">ENTENDA O LUGAR</span><div class="guide-section-heading"><h2>A história por trás da paisagem</h2>${'speechSynthesis' in window?'<button class="text-btn" id="listenHistory">◖ Ouvir história</button>':''}</div>${guide.history.length?guide.history.map(p=>`<p>${esc(p)}</p>`).join(''):'<p>Este passeio ainda não tem um guia editorial. Consulte os detalhes e as contribuições do grupo abaixo.</p>'}</section>
  <section id="guide-route" class="guide-section"><span class="eyebrow">UM PERCURSO POSSÍVEL</span><h2>O que observar, passo a passo</h2><p class="guide-muted">Sequência sugerida para a visita; adapte ao ritmo do grupo.</p><ol class="guide-route">${guide.stops.map((s,i)=>`<li><span>${String(i+1).padStart(2,'0')}</span><div><h3>${esc(s.title)}</h3><p>${esc(s.text)}</p></div></li>`).join('')}</ol></section>
  <section id="guide-gallery" class="guide-section"><span class="eyebrow">ANTES DE ESTAR LÁ</span><h2>Um olhar sobre o destino</h2><div class="guide-gallery">${photos.map((p,i)=>`<figure><button class="gallery-photo" data-gallery="${i}" aria-label="Ampliar foto: ${esc(p.alt)}"><img src="${esc(p.src)}" alt="${esc(p.alt)}" loading="lazy"><span>↗</span></button><figcaption><strong>${esc(p.caption)}</strong>${photoCredit(p)}</figcaption></figure>`).join('')||'<p>As fotos do grupo aparecerão na seção de memórias.</p>'}</div><div class="photo-tip"><span>▧</span><div><h3>Um bom olhar para a sua foto</h3><p>${esc(guide.photo_tip)}</p></div></div><small>Fotos de referência do acervo Wikimedia Commons; podem retratar o local em outra época. Redimensionamento e enquadramento para exibição; as licenças originais são mantidas.</small></section>
  <section id="guide-tips" class="guide-section"><span class="eyebrow">PARA APROVEITAR MELHOR</span><h2>Recomendações para a visita</h2><ul class="guide-tips">${guide.tips.map(t=>`<li><span>✓</span>${esc(t)}</li>`).join('')}</ul><div class="guide-access"><h3>Mobilidade e conforto</h3><p>${esc(guide.accessibility)}</p></div></section>
  ${guide.venues?.length?`<section class="guide-section guide-venues" aria-label="Vinícolas e maisons"><span class="eyebrow">VINÍCOLAS E MAISONS</span><h2>Compare as opções para a visita</h2><p>Uma escolha por dia. Nenhuma reserva foi efetuada.</p>${guide.venues.map(v=>`<article class="panel"><h3>${esc(v.name)}</h3><p>${esc(v.text)}</p><div class="guide-access"><h4>Mobilidade e conforto</h4><p>${esc(v.access)}</p></div><a class="source-link" href="${esc(v.url)}" target="_blank" rel="noopener">Consultar site oficial <span>...</span></a></article>`).join('')}</section>`:''}
  <section class="guide-section"><span class="eyebrow">INFORMAÇÃO DO SEU ROTEIRO</span><h2>O que combinamos</h2>${planningNotes(e.description)}${state.user.role==='admin'?'<button class="text-btn" id="editGuideEntry">Editar horário e detalhes ↗</button>':''}<div class="media-grid">${e.files.map(media).join('')}</div></section>
  <section id="guide-community" class="guide-section"><span class="eyebrow">ESSA HISTÓRIA TAMBÉM É NOSSA</span><div class="guide-section-heading"><h2>Memórias deste passeio</h2><button class="primary" id="publishGuideMemory">＋ Fotos e relato</button></div><p>As publicações continuam no perfil de cada viajante e ficam reunidas aqui.</p>${memories.length?`<div class="card-grid guide-memories">${memories.map(card).join('')}</div>`:'<div class="guide-memory-empty">▧ Ainda não há memórias deste passeio. Publique a primeira foto ou relato.</div>'}<h3 class="guide-conversation">Conversa do grupo <span class="count-note">${e.comments.length} comentários</span></h3><div>${e.comments.map(c=>`<div class="comment"><strong class="author-label">${avatarHtml({name:c.author,photo:c.author_photo})}${esc(c.author)}</strong><p>${esc(c.body)}</p><small>${date(c.created)} ${time(c.created)}</small></div>`).join('')||'<p>Compartilhe uma dúvida, dica ou sugestão para o grupo.</p>'}</div><form id="guideCommentForm"><label>Seu comentário<textarea name="body" required maxlength="4000" rows="3" placeholder="Uma dica, uma pergunta, uma descoberta…"></textarea></label><p class="error" id="guideCommentError"></p><button class="primary">Enviar comentário</button></form></section>
  ${guide.food?`<section class="guide-section"><span class="eyebrow">PAUSA PARA O GRUPO</span><h2>Alimentação e descanso</h2><p>${esc(guide.food)}</p></section>`:''}${guideAlternatives(guide)}<section class="guide-section guide-sources"><span class="eyebrow">CONTINUE A DESCOBERTA</span><h2>Guias, reservas e fontes oficiais</h2><p>História e referências de visita nas instituições responsáveis. Os horários do roteiro são sugestões; consulte disponibilidade, tarifas e condições atuais nos links oficiais.</p>${officialLinks(guide)}${guide.reviewed?`<small>Conteúdo editorial revisado em ${fullDate(guide.reviewed)}. As recomendações de percurso são propostas do Plantrip.</small>`:''}</section></div>
  <aside class="guide-practical"><span class="eyebrow">SUA VISITA EM RESUMO</span><h2>Prepare o caminho.</h2><dl><dt>QUANDO</dt><dd>${date(e.start)} · ${time(e.start)||'Horário a definir'}${time(e.end)?' — '+time(e.end):''}</dd><dt>TEMPO SUGERIDO</dt><dd>${esc(guide.duration)}</dd><dt>COMO CHEGAR</dt><dd>${esc(guide.arrival)}</dd><dt>INGRESSOS E ACESSO</dt><dd>${esc(guide.booking)}</dd></dl><a class="source-link" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(guide.map_query||e.title+' '+e.place)}" target="_blank" rel="noopener">Ver região no mapa <span>↗</span></a><button class="primary" id="sideShow">▷ Conhecer em slides</button><p class="count-note">Mapa externo. Confirme o ponto exato de entrada nos links oficiais.</p></aside></div>
  <div class="guide-pagination">${index>0?`<button class="text-btn" data-guide-nav="${next[index-1].id}">← ${esc(next[index-1].title)}</button>`:'<span></span>'}${index>=0&&index<next.length-1?`<button class="text-btn" data-guide-nav="${next[index+1].id}">${esc(next[index+1].title)} →</button>`:''}</div>`;
  $('#backToTours').onclick=()=>{leaveAttraction();go('tour')};$('#printGuide').onclick=()=>window.print();
  $('#startGuideShow').onclick=$('#sideShow').onclick=()=>startGuideDeck(e,guide);
  document.querySelectorAll('[data-gallery]').forEach(b=>b.onclick=()=>{guideDeck=photos.map(p=>({title:p.caption,text:p.modified,photo:p}));guideSlide=Number(b.dataset.gallery);showGuideSlide();$('#guideSlideshow').showModal()});
  document.querySelectorAll('[data-guide-nav]').forEach(b=>b.onclick=ev=>{ev.stopPropagation();openAttraction(b.dataset.guideNav,true,'place')});
  bindGuideDayMap(e,guide);
  if($('#listenHistory'))$('#listenHistory').onclick=()=>{const b=$('#listenHistory');if(speechSynthesis.speaking){speechSynthesis.cancel();b.textContent='◖ Ouvir história';return}const utterance=new SpeechSynthesisUtterance(guide.history.join(' '));utterance.lang='pt-BR';utterance.onend=()=>b.textContent='◖ Ouvir história';speechSynthesis.speak(utterance);b.textContent='■ Parar leitura'};
  if($('#editGuideEntry'))$('#editGuideEntry').onclick=()=>openEditor(e);
  $('#publishGuideMemory').onclick=()=>openMemoryEditor(null,e);
  $('#guideCommentForm').onsubmit=async ev=>{ev.preventDefault();const b=ev.target.querySelector('button');b.disabled=true;try{await api('/api/comments',{entry_id:e.id,body:ev.target.elements.body.value});await load();$('#guide-community').scrollIntoView({behavior:'smooth'});toast('Comentário enviado.')}catch(ex){$('#guideCommentError').textContent=ex.message;b.disabled=false}};
  bindActions();
}
function startGuideDeck(e,g){
  const pic=i=>g.photos[i%Math.max(g.photos.length,1)];
  guideDeck=[{title:e.title,text:g.intro,photo:pic(0),eyebrow:'CONHEÇA O DESTINO'},...g.history.map((text,i)=>({title:i?'Uma nova forma de olhar':'A história do lugar',text,photo:pic(i),eyebrow:'CONTEXTO HISTÓRICO'})),...g.stops.map((s,i)=>({title:s.title,text:s.text,photo:pic(i),eyebrow:'O QUE OBSERVAR · '+(i+1)})),{title:'Antes de sair',text:g.tips.join('\n\n'),photo:pic(1),eyebrow:'RECOMENDAÇÕES'},{title:'Agora é com vocês.',text:'Converse com o grupo, confirme as reservas e registre a sua versão desta história.',photo:pic(0),eyebrow:date(e.start)+' · '+time(e.start)}];
  guideSlide=0;showGuideSlide();$('#guideSlideshow').showModal()
}
function showGuideSlide(){const s=guideDeck[guideSlide];$('#guideSlideContent').innerHTML=`<div class="guide-slide-photo">${s.photo?`<img src="${esc(s.photo.src)}" alt="${esc(s.photo.alt)}"><div>${photoCredit(s.photo)}</div>`:''}</div><div class="guide-slide-copy"><span class="eyebrow">${esc(s.eyebrow||'GALERIA DO PASSEIO')}</span><h2>${esc(s.title)}</h2><p>${esc(s.text)}</p></div>`;$('#guideSlideCount').textContent=`${guideSlide+1} / ${guideDeck.length}`;$('#guideSlidePrev').disabled=guideSlide===0;$('#guideSlideNext').disabled=guideSlide===guideDeck.length-1}
function initAttractionControls(){
  $('#guideSlidePrev').onclick=()=>{if(guideSlide>0){guideSlide--;showGuideSlide()}};
  $('#guideSlideNext').onclick=()=>{if(guideSlide<guideDeck.length-1){guideSlide++;showGuideSlide()}};
  document.addEventListener('keydown',e=>{if($('#guideSlideshow').open){if(e.key==='ArrowRight')$('#guideSlideNext').click();if(e.key==='ArrowLeft')$('#guideSlidePrev').click()}});
  window.addEventListener('popstate',()=>{if('speechSynthesis' in window)speechSynthesis.cancel();load().catch(e=>toast(e.message))});
}
