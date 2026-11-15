// Mapa mundi das viagens: usado na página pública e na área logada (um contexto por mapa).
const LEAFLET_ASSETS={css:['https://unpkg.com/leaflet@1.9.4/dist/leaflet.css','sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY='],js:['https://unpkg.com/leaflet@1.9.4/dist/leaflet.js','sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=']};
const MAP_LEVELS={trip:{label:'VIAGEM',min:0,max:4},city:{label:'CIDADE',min:5,max:9},attraction:{label:'LOCAL VISITADO',min:10,max:99},origin:{label:'PONTO DE PARTIDA',min:0,max:99}};
const MAP_WORLD_VIEW=[[25,10],2];
const MAP_TILES=['https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}];
let leafletLoading=null,activeMapCtx=null,mapDetailMap=null;
function mapContext(prefix,source,tripFilter){return {prefix,source,tripFilter,map:null,layers:{},posts:[],trip:null,ready:false}}
const publicMapCtx=mapContext('public',()=>publicDiaryData?.map,()=>$('#publicTrip')?.value||'');
const privateMapCtx=mapContext('private',()=>state?.map,()=>'');
function loadLeaflet(){
  if(window.L)return Promise.resolve();
  if(leafletLoading)return leafletLoading;
  leafletLoading=new Promise((resolve,reject)=>{
    const link=document.createElement('link');link.rel='stylesheet';link.href=LEAFLET_ASSETS.css[0];link.integrity=LEAFLET_ASSETS.css[1];link.crossOrigin='';document.head.append(link);
    const script=document.createElement('script');script.src=LEAFLET_ASSETS.js[0];script.integrity=LEAFLET_ASSETS.js[1];script.crossOrigin='';
    script.onload=resolve;script.onerror=()=>reject(new Error('Leaflet indisponível'));document.head.append(script);
  }).catch(error=>{leafletLoading=null;throw error});
  return leafletLoading;
}
function mapMarkup(prefix,intro='Amplie o mapa para ir da viagem às cidades e aos pontos visitados. Toque em um ponto para abrir as fotos.'){return `<section class="public-map" aria-labelledby="${prefix}MapTitle"><div class="public-map-heading"><div><span class="eyebrow">MAPA MUNDI</span><h2 id="${prefix}MapTitle">Onde as histórias aconteceram</h2><p>${intro}</p></div><div class="public-map-actions"><button type="button" id="${prefix}MapWorld">◌ Mundo</button><button type="button" id="${prefix}MapFit">⌖ Ir aos pontos</button>${prefix==='private'&&isAdminUser()?'<button type="button" class="map-admin-btn" id="privatePoiManage">◎ Pontos de interesse</button>':''}</div></div><div id="${prefix}MapCanvas" class="map-canvas" role="region" aria-label="Mapa mundi com as viagens e os pontos visitados"></div><p id="${prefix}MapStatus" class="public-map-status" role="status"></p></section>`}
function publicMapMarkup(){return mapMarkup('public')}
function mapMediaCount(entries){return entries.reduce((n,e)=>n+(e.files||[]).filter(f=>/^(image|video)\//.test(f.mime)).length,0)}
function mapCountLabel(count){return `${count} ${count===1?'foto/vídeo':'fotos/vídeos'}`}
// Só administrador: editar um ponto cadastrado ou promover o local livre de uma memória a ponto de interesse.
function mapAdminPointButton(point,entries){
  if(typeof isAdminUser!=='function'||!isAdminUser())return '';
  if(point.poi_id!=null)return '<div class="map-gallery-actions"><button type="button" data-point-admin>✎ Editar ponto de interesse</button></div>';
  if(String(point.id).startsWith('g-')&&entries.length)return '<div class="map-gallery-actions"><button type="button" data-point-admin>◎ Transformar em ponto de interesse</button></div>';
  return '';
}
function mapPointKind(point){return point.level==='attraction'&&point.kind==='poi'?'poi':point.level}
function mapPinSize(point){return ({trip:[52,52],city:[40,40],attraction:[32,32],poi:[36,36],origin:[38,38]})[mapPointKind(point)]}
function mapPinGlyph(point,count){const kind=mapPointKind(point);return kind==='origin'?'✈':kind==='poi'&&!count?'★':count||'·'}
function mapDay(iso){return String(iso||'').slice(0,10).split('-').reverse().join('/')}
function mapDays(start,end){const a=Date.parse(start),b=Date.parse(end);return a&&b&&b>=a?Math.round((b-a)/864e5)+1:0}

async function initMap(ctx){
  const canvas=$(`#${ctx.prefix}MapCanvas`);if(!canvas)return;
  ctx.ready=false;ctx.trip=null;
  try{await loadLeaflet()}catch{if($(`#${ctx.prefix}MapCanvas`)===canvas)canvas.innerHTML='<div class="public-map-error">Não foi possível carregar o mapa agora. As memórias continuam disponíveis na lista.</div>';return}
  if($(`#${ctx.prefix}MapCanvas`)!==canvas)return;
  ctx.map?.remove();
  const map=ctx.map=L.map(canvas,{minZoom:2,maxZoom:18,worldCopyJump:true,scrollWheelZoom:false,zoomSnap:.5});
  L.tileLayer(...MAP_TILES).addTo(map);
  ctx.layers=Object.fromEntries(Object.keys(MAP_LEVELS).map(level=>[level,L.layerGroup()]));
  map.on('click focus',()=>map.scrollWheelZoom.enable());map.on('mouseout blur',()=>map.scrollWheelZoom.disable());
  map.on('zoomend',()=>syncMapLevels(ctx));
  map.setView(...MAP_WORLD_VIEW);
  $(`#${ctx.prefix}MapWorld`).onclick=()=>map.setView(...MAP_WORLD_VIEW);
  $(`#${ctx.prefix}MapFit`).onclick=()=>fitMapPoints(ctx);
  if($('#privatePoiManage'))$('#privatePoiManage').onclick=openPoiManager;
  ctx.ready=true;updateMap(ctx,ctx.posts);
}
function visibleMapPoints(ctx,posts){
  const ids=new Map(posts.map(e=>[e.id,e])),trip=ctx.tripFilter();
  return (ctx.source()?.points||[]).filter(p=>!trip||String(p.trip_id)===trip).map(p=>({point:p,entries:p.entry_ids.map(id=>ids.get(id)).filter(Boolean).sort((a,b)=>String(a.start).localeCompare(String(b.start)))})).filter(x=>x.entries.length||x.point.always);
}
function fitMapPoints(ctx){
  const cities=ctx.layers.city.getLayers().map(m=>m.getLatLng());
  if(cities.length)ctx.map.fitBounds(L.latLngBounds(cities),{padding:[50,50],maxZoom:cities.length===1?9:6});
}
function mapMarker(point,entries,onClick){
  const count=mapMediaCount(entries),[w,h]=mapPinSize(point),kind=mapPointKind(point);
  const marker=L.marker([point.lat,point.lng],{icon:L.divIcon({html:`<span class="map-pin map-pin-${kind}${count?'':' map-pin-empty'}"><b>${mapPinGlyph(point,count)}</b></span>`,className:'map-pin-wrap',iconSize:[w,h],iconAnchor:[w/2,h/2]}),title:`${point.name} · ${memoryPostCount(entries.length)}`,alt:point.name,riseOnHover:true});
  const label=kind==='origin'?`Partida · ${esc(point.name)}`:kind==='poi'?`${esc(point.name)} · ponto de interesse`:esc(point.name);
  marker.bindTooltip(`${label}${count?' · '+mapCountLabel(count):''}`,{direction:'top',offset:[0,-h/2]});
  marker.on('click',onClick);
  return marker;
}
function openMapPoint(ctx,point,entries){if(point.level==='trip'||point.level==='city')openMapDetail(ctx,point);else openMapGallery(ctx,point,entries)}
function updateMap(ctx,posts){
  ctx.posts=posts;if(!ctx.ready||!ctx.map)return;
  Object.values(ctx.layers).forEach(layer=>layer.clearLayers());
  const rows=visibleMapPoints(ctx,posts);
  for(const {point,entries} of rows)ctx.layers[point.level==='origin'?'origin':point.level].addLayer(mapMarker(point,entries,()=>openMapPoint(ctx,point,entries)));
  const trip=ctx.tripFilter();
  if(ctx.trip!==trip){
    const first=ctx.trip===null;ctx.trip=trip;
    if(trip)fitMapPoints(ctx);else if(!first)ctx.map.setView(...MAP_WORLD_VIEW);
  }
  syncMapLevels(ctx);
  const data=ctx.source()||{unlocated:[]},hidden=(data.unlocated||[]).filter(id=>posts.some(e=>e.id===id)).length,places=rows.filter(x=>x.point.level==='attraction'&&x.entries.length).length;
  $(`#${ctx.prefix}MapStatus`).textContent=!rows.length?'Nenhuma memória com localização reconhecida.':`${places} ${places===1?'ponto com fotos':'pontos com fotos'} no mapa. Aproxime para ver cidades e locais visitados.`+(hidden?` ${hidden} ${hidden===1?'memória sem localização reconhecida aparece':'memórias sem localização reconhecida aparecem'} apenas na lista.`:'');
}
function syncMapLevels(ctx){
  if(!ctx.map)return;const zoom=ctx.map.getZoom();
  for(const [level,range] of Object.entries(MAP_LEVELS)){
    const layer=ctx.layers[level],visible=zoom>=range.min&&zoom<=range.max;
    if(visible&&!ctx.map.hasLayer(layer))layer.addTo(ctx.map);
    if(!visible&&ctx.map.hasLayer(layer))ctx.map.removeLayer(layer);
  }
}
// Compatibilidade com a página pública.
function initPublicMap(){return initMap(publicMapCtx)}
function updatePublicMap(posts){updateMap(publicMapCtx,posts)}

function mapDetailChildren(ctx,point){
  const rows=visibleMapPoints(ctx,ctx.posts);
  return point.level==='trip'?rows.filter(x=>x.point.level==='city'&&x.point.trip_id===point.trip_id):rows.filter(x=>x.point.level==='attraction'&&x.point.trip_id===point.trip_id&&x.point.city===point.name);
}
function mapSummaryHtml(ctx,point,rows,self){
  const trip=(ctx.source()?.trips||[]).find(t=>t.id===point.trip_id)||{},mine=rows.filter(x=>x.point.trip_id===point.trip_id);
  const visited=mine.filter(x=>x.point.level==='attraction'&&x.point.kind!=='poi'),interest=mine.filter(x=>x.point.kind==='poi'),origin=mine.find(x=>x.point.level==='origin');
  const withPhotos=visited.filter(x=>x.entries.length).length,days=mapDays(trip.start,trip.end);
  const byCity=new Map();for(const x of visited){if(!byCity.has(x.point.city))byCity.set(x.point.city,[]);byCity.get(x.point.city).push(x)}
  const item=x=>`<li><button type="button" data-summary-point="${esc(x.point.id)}"><span>${esc(x.point.name)}</span><small>${x.entries.length?mapCountLabel(mapMediaCount(x.entries)):'sem fotos'}</small></button></li>`;
  const row=(label,body)=>`<div><dt>${label}</dt><dd>${body}</dd></div>`;
  return `<div class="map-summary" role="complementary" aria-label="Resumo da viagem"><h3>Resumo da viagem</h3><dl>${row('Período',`${mapDay(trip.start)} → ${mapDay(trip.end)}${days?`<small>${days} dias</small>`:''}`)}${trip.route?.length?row('Roteiro',esc(trip.route.join(' → '))):''}${row('Países visitados',(trip.countries||[]).length?`<ul class="map-chips">${trip.countries.map(c=>`<li>${esc(c)}</li>`).join('')}</ul>`:'—')}${origin?row('Partida',`${esc(origin.point.name)}, ${esc(origin.point.country||trip.origin?.country||'')}<button type="button" class="text-btn" data-summary-point="${esc(origin.point.id)}">Ver no mapa ↗</button>`):''}${row('Fotos',`${mapCountLabel(mapMediaCount(self.entries))} em ${memoryPostCount(self.entries.length)}`)}</dl>
  <h4>Pontos visitados <span>${visited.length}${visited.length?` · ${withPhotos} com fotos`:''}</span></h4>${visited.length?[...byCity].map(([city,list],i)=>`<details${i===0?' open':''}><summary>${esc(city)} <small>${list.length}</small></summary><ul>${list.map(item).join('')}</ul></details>`).join(''):'<p class="map-summary-empty">Nenhum ponto registrado ainda.</p>'}
  ${interest.length?`<h4>Pontos de interesse</h4><ul class="map-summary-interest">${interest.map(item).join('')}</ul>`:''}</div>`;
}
function openMapDetail(ctx,point){
  activeMapCtx=ctx;
  const all=visibleMapPoints(ctx,ctx.posts),self=all.find(x=>x.point.id===point.id);if(!self)return;
  const children=mapDetailChildren(ctx,point),isTrip=point.level==='trip',parent=isTrip?null:all.find(x=>x.point.level==='trip'&&x.point.trip_id===point.trip_id);
  let dialog=$('#mapDetail');
  if(!dialog){dialog=document.createElement('dialog');dialog.id='mapDetail';dialog.className='map-detail';document.body.append(dialog);dialog.addEventListener('close',()=>{mapDetailMap?.remove();mapDetailMap=null})}
  dialog.setAttribute('aria-label',`Mapa de ${point.name}`);dialog.classList.toggle('map-detail-wide',isTrip);
  const total=mapMediaCount(self.entries),places=children.filter(x=>x.point.level==='attraction');
  const childLabel=isTrip?'Cidades':'Pontos visitados';
  dialog.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">${MAP_LEVELS[point.level].label}</span><h2>${esc(point.name)}</h2><p class="map-gallery-count">${children.length} ${isTrip?(children.length===1?'cidade':'cidades'):(children.length===1?'ponto':'pontos')} · ${memoryPostCount(self.entries.length)} · ${mapCountLabel(total)}</p></div><button type="button" class="close" data-detail-close aria-label="Fechar mapa">×</button></div><div class="map-gallery-actions">${parent?`<button type="button" data-detail-parent>← ${esc(parent.point.name)}</button>`:''}<button type="button" data-detail-all>▧ Ver todas as fotos</button><button type="button" data-detail-clip>▷ Miniclipe</button></div><div class="map-detail-layout"><div class="map-detail-main"><div id="mapDetailCanvas" role="region" aria-label="Mapa ampliado de ${esc(point.name)}"></div><h3 class="map-detail-subtitle">${childLabel}</h3><ol class="map-detail-list">${children.map((x,i)=>{const cover=coverOf(x.entries);return `<li><button type="button" data-detail-child="${i}">${cover?`<img src="${mediaUrl(cover,480)}" alt="" loading="lazy">`:'<span class="map-detail-noimg">⌖</span>'}<span><strong>${esc(x.point.name)}</strong><small>${x.entries.length?memoryPostCount(x.entries.length)+' · '+mapCountLabel(mapMediaCount(x.entries)):'sem fotos ainda'}</small><em>${isTrip?'Abrir mapa da cidade →':x.entries.length?'Ver fotos →':'Ver informações →'}</em></span></button></li>`}).join('')}</ol></div>${isTrip?mapSummaryHtml(ctx,point,all,self):''}</div>`;
  const openChild=x=>isTrip?openMapDetail(ctx,x.point):openMapGallery(ctx,x.point,x.entries);
  dialog.querySelector('[data-detail-close]').onclick=()=>dialog.close();
  dialog.querySelector('[data-detail-all]').onclick=()=>openMapGallery(ctx,point,self.entries);
  dialog.querySelector('[data-detail-clip]').onclick=()=>presentMemories(self.entries,true);
  if(parent)dialog.querySelector('[data-detail-parent]').onclick=()=>openMapDetail(ctx,parent.point);
  dialog.querySelectorAll('[data-detail-child]').forEach(b=>b.onclick=()=>openChild(children[Number(b.dataset.detailChild)]));
  if(!dialog.open)dialog.showModal();dialog.scrollTop=0;
  mapDetailMap?.remove();
  const map=mapDetailMap=L.map('mapDetailCanvas',{minZoom:2,maxZoom:18,scrollWheelZoom:true,zoomSnap:.5});
  L.tileLayer(...MAP_TILES).addTo(map);
  const cityLayer=L.layerGroup(),pointLayer=L.layerGroup(),originLayer=L.layerGroup().addTo(map);
  const mine=all.filter(x=>x.point.trip_id===point.trip_id);
  const markers=new Map();
  for(const x of mine){
    if(x.point.level==='origin')originLayer.addLayer(mapMarker(x.point,x.entries,()=>openMapGallery(ctx,x.point,x.entries)));
    else if(isTrip&&x.point.level==='city')cityLayer.addLayer(mapMarker(x.point,x.entries,()=>openMapDetail(ctx,x.point)));
    else if(x.point.level==='attraction'&&(isTrip||x.point.city===point.name)){const m=mapMarker(x.point,x.entries,()=>openMapGallery(ctx,x.point,x.entries));markers.set(x.point.id,m);pointLayer.addLayer(m)}
  }
  const sync=()=>{
    const close=map.getZoom()>=11||!isTrip;
    if(isTrip){if(close&&map.hasLayer(cityLayer))map.removeLayer(cityLayer);if(!close&&!map.hasLayer(cityLayer))cityLayer.addTo(map)}
    if(close&&!map.hasLayer(pointLayer))pointLayer.addTo(map);if(!close&&map.hasLayer(pointLayer))map.removeLayer(pointLayer);
  };
  map.on('zoomend',sync);
  const coords=children.map(x=>[x.point.lat,x.point.lng]);
  if(coords.length>1)map.fitBounds(coords,{padding:[45,45],maxZoom:15});else map.setView(coords[0]||[point.lat,point.lng],isTrip?6:14);
  sync();requestAnimationFrame(()=>map.invalidateSize());
  dialog.querySelectorAll('[data-summary-point]').forEach(b=>b.onclick=()=>{
    const x=all.find(y=>y.point.id===b.dataset.summaryPoint);if(!x)return;
    if(x.entries.length&&x.point.level==='attraction'&&x.point.kind!=='poi')return openMapGallery(ctx,x.point,x.entries);
    map.flyTo([x.point.lat,x.point.lng],x.point.level==='origin'?5:15,{duration:.8});
    L.popup({closeButton:false,offset:[0,-14]}).setLatLng([x.point.lat,x.point.lng]).setContent(`<strong>${esc(x.point.name)}</strong>${x.point.text?`<br><small>${esc(x.point.text)}</small>`:''}${x.entries.length?'':'<br><small>Sem fotos ainda.</small>'}`).openOn(map);
    document.querySelector('#mapDetailCanvas')?.scrollIntoView({block:'nearest',behavior:'smooth'});
  });
}
function openMapGallery(ctx,point,entries){
  activeMapCtx=ctx;
  let dialog=$('#mapGallery');
  if(!dialog){dialog=document.createElement('dialog');dialog.id='mapGallery';dialog.className='map-gallery';dialog.setAttribute('aria-label','Fotos do ponto selecionado');document.body.append(dialog)}
  const total=mapMediaCount(entries),kind=mapPointKind(point);
  dialog.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">${kind==='poi'?'PONTO DE INTERESSE':MAP_LEVELS[point.level].label}</span><h2>${esc(point.name)}</h2><p class="map-gallery-count">${entries.length?`${memoryPostCount(entries.length)} · ${mapCountLabel(total)}`:'Ainda sem fotos neste ponto'}</p></div><button type="button" class="close" data-map-close aria-label="Fechar fotos">×</button></div>${point.text?`<p class="map-gallery-text">${esc(point.text)}</p>`:''}${mapAdminPointButton(point,entries)}${entries.length?'<div class="map-gallery-actions"><button type="button" data-map-slides>▧ Ver slides</button><button type="button" data-map-clip>▷ Ver miniclipe</button></div>':''}${entries.map(e=>`<article class="map-gallery-memory"><h3>${esc(e.title)}</h3><p>${esc(e.author)} · ${date(e.start)}${e.place?' · '+esc(e.place):''}</p>${e.description?`<p class="map-gallery-text">${esc(e.description)}</p>`:''}${memoryGallery(e)}</article>`).join('')}`;
  dialog.querySelector('[data-map-close]').onclick=()=>dialog.close();
  dialog.querySelector('[data-point-admin]')?.addEventListener('click',()=>{dialog.close();openPoiEditor(point.poi_id!=null?poiFromPoint(point):poiPrefillFor(entries[0]))});
  if(entries.length){
    dialog.querySelector('[data-map-slides]').onclick=()=>presentMemories(entries,false);
    dialog.querySelector('[data-map-clip]').onclick=()=>presentMemories(entries,true);
  }
  dialog.querySelectorAll('[data-memory-thumbnail]').forEach(b=>b.onclick=()=>presentMemories(entries,false,Number(b.dataset.memoryFile)));
  dialog.scrollTop=0;if(!dialog.open)dialog.showModal();
}
