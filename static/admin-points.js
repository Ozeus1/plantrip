// Ferramentas do administrador: editar uma foto (mover, capa, excluir) e cadastrar/editar pontos de interesse.
const isAdminUser=()=>typeof state!=='undefined'&&state?.user?.role==='admin';
function adminDialog(id,label){
  let d=document.getElementById(id);
  if(!d){d=document.createElement('dialog');d.id=id;d.className='admin-dialog';d.setAttribute('aria-label',label);document.body.append(d)}
  return d;
}

// ---------- Foto: mover para outra memória, capa e exclusão ----------
function movableMemories(entry){
  return (state.entries||[]).filter(e=>e.kind==='diary'&&e.id!==entry.id&&e.trip_id===entry.trip_id&&(e.files||[]).some(f=>/^(image|video)\//.test(f.mime)))
    .sort((a,b)=>String(a.place||'').localeCompare(String(b.place||''),'pt-BR')||String(a.title).localeCompare(String(b.title),'pt-BR'));
}
// onDone({action:'moved'|'deleted'|'cover', target?}) é chamado depois que o servidor confirmou.
function openPhotoAdmin(entry,file,onDone=()=>{}){
  if(!isAdminUser())return;
  const d=adminDialog('photoAdmin','Editar foto'),targets=entry.trip_id===state.trip_id?movableMemories(entry):[],video=file.mime.startsWith('video/');
  d.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">EDITAR ${video?'CLIPE':'FOTO'}</span><h2>${esc(file.name)}</h2><p class="admin-sub">${esc(entry.title)}${entry.place?' · '+esc(entry.place):''}</p></div><button type="button" class="close" data-admin-close aria-label="Fechar">×</button></div>
  ${video?'':`<img class="admin-photo" src="${mediaUrl(file,480)}" alt="">`}
  <p class="error" id="photoAdminError" role="alert"></p>
  <section class="admin-block"><h3>Atribuir a outro ponto de visita</h3>${targets.length?`<label>Mover para a memória<select id="photoMoveTo">${targets.map(t=>`<option value="${t.id}">${esc(t.place||'Sem local')} · ${esc(t.title)} (${(t.files||[]).length})</option>`).join('')}</select></label><button type="button" class="primary" id="photoMove">Mover ${video?'clipe':'foto'}</button>`:'<p class="admin-sub">Não há outras memórias com fotos nesta viagem para receber este arquivo.</p>'}</section>
  <section class="admin-block admin-row">${video?'':`<button type="button" id="photoCover" ${entry.cover_file_id===file.id?'disabled':''}>${entry.cover_file_id===file.id?'★ Já é a capa':'☆ Usar como capa'}</button>`}${typeof openPhotoEditor==='function'&&photoEditable(file)?'<button type="button" id="photoEdit">✂ Editar imagem…</button>':''}<button type="button" id="photoPoi">◎ Ponto de interesse…</button></section>
  <section class="admin-block"><button type="button" class="text-btn danger" id="photoDelete">Excluir do site</button></section>`;
  const fail=ex=>{$('#photoAdminError').textContent=ex.message};
  const done=async(info,message)=>{d.close();try{await onDone(info)}finally{toast(message)}};
  d.querySelector('[data-admin-close]').onclick=()=>d.close();
  if(targets.length)$('#photoMove').onclick=async()=>{
    const to=Number($('#photoMoveTo').value),target=targets.find(t=>t.id===to);
    try{await api('/api/files/move',{entry_id:entry.id,file_id:file.id,to_entry_id:to});await done({action:'moved',target},'Movido para “'+(target.place||target.title)+'”.')}catch(ex){fail(ex)}
  };
  if($('#photoCover'))$('#photoCover').onclick=async()=>{try{await api('/api/files/arrange',{entry_id:entry.id,cover_file_id:file.id});await done({action:'cover'},'Capa atualizada.')}catch(ex){fail(ex)}};
  if($('#photoEdit'))$('#photoEdit').onclick=()=>{d.close();openPhotoEditor(entry,file,onDone)};
  $('#photoPoi').onclick=()=>{d.close();openPoiEditor(poiPrefillFor(entry))};
  $('#photoDelete').onclick=async()=>{
    if(!confirm('Excluir este arquivo do site? Esta ação não pode ser desfeita.'))return;
    try{await api('/api/delete-file',{entry_id:entry.id,file_id:file.id});await done({action:'deleted'},'Arquivo excluído.')}catch(ex){fail(ex)}
  };
  if(!d.open)d.showModal();
}

// ---------- Pontos de interesse ----------
function poiPrefillFor(entry){
  // Parte do que já se sabe: nome do local digitado, cidade e coordenadas do ponto onde a memória caiu no mapa.
  const point=(state.map?.points||[]).find(p=>p.level==='attraction'&&(p.entry_ids||[]).includes(entry.id));
  if(point?.poi_id)return {id:point.poi_id,name:point.name,city:point.city,country:point.country||'',lat:point.lat,lng:point.lng,text:point.text||'',aliases:point.aliases||[],trip_id:entry.trip_id};
  return {name:String(entry.place||entry.title||'').trim(),city:point?.city||'',lat:point?.lat??'',lng:point?.lng??'',text:'',aliases:[],trip_id:entry.trip_id,withEntry:entry.id};
}
function poiFromPoint(point){return {id:point.poi_id,name:point.name,city:point.city,country:point.country||'',lat:point.lat,lng:point.lng,text:point.text||'',aliases:point.aliases||[],trip_id:point.trip_id}}

let poiPicker=null;
async function openPoiManager(){
  if(!isAdminUser())return;
  const d=adminDialog('poiManager','Pontos de interesse');
  d.innerHTML='<div class="modal-heading"><h2>Pontos de interesse</h2><button type="button" class="close" data-admin-close aria-label="Fechar">×</button></div><p class="admin-sub">Carregando…</p>';
  if(!d.open)d.showModal();d.querySelector('[data-admin-close]').onclick=()=>d.close();
  try{
    const {pois}=await api('/api/pois'),trips=Object.fromEntries((state.trips||[]).map(t=>[t.id,t.name]));
    d.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">ADMINISTRAÇÃO</span><h2>Pontos de interesse</h2></div><button type="button" class="close" data-admin-close aria-label="Fechar">×</button></div>
    <p class="admin-sub">Locais que aparecem no mapa com título, texto e fotos. Memórias cujo local tenha o nome (ou um nome alternativo) do ponto passam a ser mostradas nele.</p>
    <button type="button" class="primary" id="poiNew">＋ Novo ponto de interesse</button>
    <ul class="admin-list">${pois.map(p=>`<li><button type="button" data-poi-edit="${p.id}"><strong>${esc(p.name)}</strong><small>${esc(p.city)} · ${esc(trips[p.trip_id]||'Viagem')}</small></button></li>`).join('')||'<li class="admin-sub">Nenhum ponto cadastrado ainda.</li>'}</ul>`;
    d.querySelector('[data-admin-close]').onclick=()=>d.close();
    $('#poiNew').onclick=()=>{d.close();openPoiEditor({trip_id:state.trip_id})};
    d.querySelectorAll('[data-poi-edit]').forEach(b=>b.onclick=()=>{d.close();openPoiEditor(pois.find(p=>p.id===Number(b.dataset.poiEdit)))});
  }catch(ex){d.querySelector('.admin-sub').textContent=ex.message}
}

async function openPoiEditor(poi={}){
  if(!isAdminUser())return;
  const d=adminDialog('poiEditor','Ponto de interesse');
  let cities=[];try{cities=(await api('/api/pois')).cities}catch{}
  const editing=poi.id!=null,aliases=(poi.aliases||[]).join(', '),tripId=poi.trip_id??state.trip_id;
  d.innerHTML=`<form id="poiForm"><div class="modal-heading"><div><span class="eyebrow">${editing?'EDITAR':'NOVO'} PONTO DE INTERESSE</span><h2>${esc(poi.name||'Novo ponto')}</h2></div><button type="button" class="close" data-admin-close aria-label="Fechar">×</button></div>
  <label>Título do ponto<input name="name" required maxlength="120" value="${esc(poi.name||'')}"></label>
  <label>Viagem<select name="trip_id">${(state.trips||[]).map(t=>`<option value="${t.id}" ${t.id===tripId?'selected':''}>${esc(t.name)}</option>`).join('')}</select></label>
  <div class="admin-two"><label>Cidade<input name="city" required maxlength="80" list="poiCities" value="${esc(poi.city||'')}" autocomplete="off"></label><label>País <small>(só para cidade nova)</small><input name="country" maxlength="80" value="${esc(poi.country||'')}"></label></div>
  <datalist id="poiCities">${cities.map(c=>`<option value="${esc(c.name)}">${esc(c.country)}</option>`).join('')}</datalist>
  <div class="admin-two"><label>Latitude<input name="lat" required inputmode="decimal" value="${esc(poi.lat??'')}" placeholder="48.8867"></label><label>Longitude<input name="lng" required inputmode="decimal" value="${esc(poi.lng??'')}" placeholder="2.3431"></label></div>
  <p class="admin-sub">Clique no mapa para posicionar o ponto (ou digite as coordenadas).</p><div id="poiPicker" class="admin-picker"></div>
  <label>Texto de apresentação<textarea name="text" rows="4" maxlength="4000" placeholder="História, dicas, por que visitar…">${esc(poi.text||'')}</textarea></label>
  <label>Outros nomes que as memórias podem usar <small>(separados por vírgula)</small><input name="aliases" maxlength="900" value="${esc(aliases)}"></label>
  <label>Adicionar fotos ao ponto<input name="photos" type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,image/heic,image/heif,video/mp4,video/webm,video/quicktime"></label>
  <p class="error" id="poiError" role="alert"></p>
  <div class="admin-row"><button class="primary" id="poiSave">${editing?'Salvar ponto':'Criar ponto'}</button>${editing?'<button type="button" class="text-btn danger" id="poiDelete">Excluir ponto</button>':''}<button type="button" class="text-btn" data-admin-close>Cancelar</button></div></form>`;
  const form=$('#poiForm');
  d.querySelectorAll('[data-admin-close]').forEach(b=>b.onclick=()=>d.close());
  // Cidade conhecida preenche país e, se vazio, o centro da cidade.
  form.elements.city.onchange=()=>{const c=cities.find(x=>x.name.toLocaleLowerCase('pt-BR')===form.elements.city.value.trim().toLocaleLowerCase('pt-BR'));if(!c)return;form.elements.country.value=c.country;if(!form.elements.lat.value&&!form.elements.lng.value){form.elements.lat.value=c.lat;form.elements.lng.value=c.lng;placePicker()}};
  let marker=null,pickMap=null;
  const num=v=>Number(String(v).replace(',','.'));
  function placePicker(){
    if(!pickMap)return;const lat=num(form.elements.lat.value),lng=num(form.elements.lng.value);
    if(!Number.isFinite(lat)||!Number.isFinite(lng)||form.elements.lat.value===''||form.elements.lng.value==='')return;
    if(!marker)marker=L.marker([lat,lng],{draggable:true}).addTo(pickMap).on('dragend',()=>setPoint(marker.getLatLng()));else marker.setLatLng([lat,lng]);
    pickMap.setView([lat,lng],Math.max(pickMap.getZoom(),13));
  }
  function setPoint(ll){form.elements.lat.value=ll.lat.toFixed(5);form.elements.lng.value=ll.lng.toFixed(5);placePicker()}
  form.elements.lat.onchange=form.elements.lng.onchange=placePicker;
  if(!d.open)d.showModal();
  loadLeaflet().then(()=>{
    if(!d.open)return;
    pickMap=L.map('poiPicker',{worldCopyJump:true}).setView([30,10],2);L.tileLayer(...MAP_TILES).addTo(pickMap);
    pickMap.on('click',e=>setPoint(e.latlng));placePicker();setTimeout(()=>pickMap?.invalidateSize(),120);
    d.addEventListener('close',()=>{pickMap?.remove();pickMap=null},{once:true});
  }).catch(()=>{$('#poiPicker').textContent='Mapa indisponível: informe as coordenadas manualmente.'});
  if(editing)$('#poiDelete').onclick=async()=>{
    if(!confirm('Excluir este ponto? As memórias e fotos continuam no site; apenas o ponto cadastrado deixa de existir.'))return;
    try{await api('/api/pois/delete',{id:poi.id});d.close();await load();toast('Ponto excluído.')}catch(ex){$('#poiError').textContent=ex.message}
  };
  form.onsubmit=async ev=>{
    ev.preventDefault();const f=form.elements,button=$('#poiSave');button.disabled=true;$('#poiError').textContent='';
    const payload={id:editing?poi.id:undefined,trip_id:Number(f.trip_id.value),name:f.name.value,city:f.city.value,country:f.country.value,lat:f.lat.value,lng:f.lng.value,text:f.text.value,aliases:f.aliases.value};
    try{
      await api('/api/pois',payload);
      const files=[...f.photos.files];
      if(files.length){
        // As fotos do ponto ficam numa memória com o nome do ponto: assim usam ordem, capa e versões leves como as demais.
        const made=await api('/api/entries',{kind:'diary',trip_id:payload.trip_id,title:payload.name,place:payload.name,start:memoryToday(),description:''});
        for(const file of files){button.textContent='Enviando '+file.name+'…';const r=await fetch('/api/upload',{method:'POST',headers:{'X-Entry-Id':String(made.id),'X-File-Name':encodeURIComponent(file.name)},body:file});if(!r.ok)throw Error((await r.json()).error||'Falha ao enviar '+file.name)}
      }
      d.close();await load();toast(editing?'Ponto atualizado.':'Ponto criado.');
    }catch(ex){$('#poiError').textContent=ex.message;button.disabled=false;button.textContent=editing?'Salvar ponto':'Criar ponto'}
  };
}
